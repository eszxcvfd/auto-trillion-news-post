import os
import openpyxl
from typing import List, Dict, Optional, Tuple
from src.models import NewsItem, BusinessWorkbookRow

# Expected mapping of normalized column headers to BusinessWorkbookRow attributes
REQUIRED_MAPPING = {
    "#": "id",
    "trillion $ news title": "title",
    "image link": "image_link",
    "linkedin": "linkedin_draft",
    "facebook": "facebook_draft",
    "x (twitter)": "x_draft",
    "instagram": "instagram_draft",
    "pinterest": "pinterest_draft",
    "threads": "threads_draft",
    "tiktok": "tiktok_draft",
    "youtube": "youtube_draft"
}

OPTIONAL_MAPPING = {
    "link post": "link_post_raw"
}


def normalize_header(header_val) -> Optional[str]:
    """
    Trim all headers before matching. Do not fail on leading or trailing whitespace.
    Convert to lowercase for robust matching.
    """
    if header_val is None:
        return None
    return str(header_val).strip().lower()


def normalize_cell_content(cell_val) -> Optional[str]:
    """
    A draft cell has 'no content' when it is:
    - Empty (None)
    - Whitespace only
    - Exactly '.'
    These are normalized to None. Otherwise return stripped string.
    """
    if cell_val is None:
        return None
    val_str = str(cell_val).strip()
    if not val_str or val_str == ".":
        return None
    return val_str


def parse_row_id(id_val) -> Optional[int]:
    """
    Normalize row ID values. Floats like 1.0 are converted to integers.
    """
    if id_val is None:
        return None
    try:
        # Convert float to int if applicable (e.g. 1.0 -> 1)
        float_val = float(id_val)
        if float_val.is_integer():
            return int(float_val)
        return int(float_val)
    except (ValueError, TypeError):
        pass
    
    # Return stripped string/original if it can't be converted to integer
    try:
        return int(str(id_val).strip())
    except (ValueError, TypeError):
        pass
    
    return id_val


def detect_workbook_type(filepath: str) -> str:
    """
    Detect whether the workbook at filepath is:
    - 'business': Contract B (multi-sheet Trillion $ news Title format)
    - 'legacy': Contract A (single-sheet 14-column ID, Found Date format)
    
    Raises FileNotFoundError if file doesn't exist.
    Raises ValueError if workbook is unrecognized or empty.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workbook file '{filepath}' does not exist.")
    
    try:
        # Load in read-only mode for fast detection
        wb = openpyxl.load_workbook(filepath, read_only=True)
    except Exception as e:
        raise ValueError(f"Failed to open workbook {filepath}: {e}")
    
    try:
        if not wb.sheetnames:
            raise ValueError(f"Workbook '{filepath}' has no sheets.")
        
        # Check active sheet (or first sheet) headers
        ws = wb.active or wb.worksheets[0]
        
        # Read the first row (headers)
        first_row = []
        for row in ws.iter_rows(max_row=1, values_only=True):
            first_row = row
            break
        
        if not first_row:
            raise ValueError(f"First sheet '{ws.title}' in workbook '{filepath}' is empty.")
        
        normalized_headers = [normalize_header(h) for h in first_row if h is not None]
        
        # Detect based on signature headers
        if "trillion $ news title" in normalized_headers:
            return "business"
        elif "id" in normalized_headers and "found date" in normalized_headers and "keyword" in normalized_headers:
            return "legacy"
        else:
            raise ValueError(
                f"Unrecognized workbook headers schema in sheet '{ws.title}'. "
                f"Found headers: {list(normalized_headers)}"
            )
    finally:
        wb.close()


def ingest_business_workbook(filepath: str, sheet_scope: Optional[List[str]] = None) -> Tuple[List[BusinessWorkbookRow], List[str]]:
    """
    Ingest a Business Workbook (Contract B) at filepath.
    
    Args:
        filepath: Path to the Excel file.
        sheet_scope: Optional list of sheet names to parse. If None, parses all valid sheets.
        
    Returns:
        A tuple: (List of BusinessWorkbookRow, List of warning/error messages)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workbook file '{filepath}' does not exist.")
        
    wb = openpyxl.load_workbook(filepath, data_only=True)
    parsed_rows: List[BusinessWorkbookRow] = []
    warnings: List[str] = []
    
    try:
        sheets_to_parse = sheet_scope if sheet_scope is not None else wb.sheetnames
        
        for name in sheets_to_parse:
            if name not in wb.sheetnames:
                warnings.append(f"Requested sheet '{name}' does not exist in workbook. Skipping.")
                continue
                
            ws = wb[name]
            
            # Read header row
            header_row = []
            for row in ws.iter_rows(max_row=1, values_only=True):
                header_row = row
                break
                
            if not header_row or all(cell is None for cell in header_row):
                warnings.append(f"Sheet '{name}' has no header row. Skipping.")
                continue
                
            # Compute header maps
            header_map: Dict[int, str] = {}
            normalized_headers_set = set()
            
            for idx, cell_val in enumerate(header_row):
                norm = normalize_header(cell_val)
                if norm is not None:
                    normalized_headers_set.add(norm)
                    # Check if this header maps to a row property
                    if norm in REQUIRED_MAPPING:
                        header_map[idx + 1] = REQUIRED_MAPPING[norm]
                    elif norm in OPTIONAL_MAPPING:
                        header_map[idx + 1] = OPTIONAL_MAPPING[norm]
            
            # Check signature header first: if it doesn't contain "trillion $ news title", 
            # assume it is a helper sheet and skip it.
            if "trillion $ news title" not in normalized_headers_set:
                warnings.append(f"Sheet '{name}' does not appear to be a category posting sheet (missing signature 'Trillion $ news Title'). Skipping.")
                continue
                
            # If it is a category posting sheet, validate all required headers are present
            missing_headers = []
            for req_header, attr in REQUIRED_MAPPING.items():
                if req_header not in normalized_headers_set:
                    missing_headers.append(req_header)
                    
            if missing_headers:
                raise ValueError(
                    f"Sheet '{name}' is missing required category posting headers: {missing_headers}"
                )
                
            # If "link post" is missing, log a warning (it is tolerated on read)
            if "link post" not in normalized_headers_set:
                warnings.append(f"Sheet '{name}' is missing 'Link Post' column. It will be tolerated, defaulting platform posting status to pending.")
                
            # Parse rows
            # We start from row index 2
            row_idx = 1
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_idx += 1
                
                # Extract values based on header_map
                row_data = {attr: None for attr in REQUIRED_MAPPING.values()}
                row_data.update({attr: None for attr in OPTIONAL_MAPPING.values()})
                
                has_any_value = False
                for cell_idx, val in enumerate(row):
                    col_num = cell_idx + 1
                    if col_num in header_map:
                        attr_name = header_map[col_num]
                        
                        if attr_name == "id":
                            row_data[attr_name] = parse_row_id(val)
                        elif attr_name == "title":
                            row_data[attr_name] = normalize_cell_content(val)
                        elif attr_name in ["linkedin_draft", "facebook_draft", "x_draft", "instagram_draft", "pinterest_draft", "threads_draft", "tiktok_draft", "youtube_draft"]:
                            cell_str = normalize_cell_content(val)
                            if cell_str:
                                from src.draft_paths import load_draft_from_cell, looks_like_file_reference

                                resolved_content = load_draft_from_cell(cell_str, filepath)
                                if resolved_content is not None:
                                    row_data[attr_name] = resolved_content
                                elif looks_like_file_reference(cell_str):
                                    platform_key = attr_name.replace("_draft", "")
                                    broken_refs = row_data.get("broken_draft_refs") or {}
                                    broken_refs[platform_key] = cell_str
                                    row_data["broken_draft_refs"] = broken_refs
                                    warnings.append(
                                        f"Row {row_idx} in sheet '{name}': draft file not found ({cell_str})"
                                    )
                                    row_data[attr_name] = None
                                else:
                                    row_data[attr_name] = cell_str
                            else:
                                row_data[attr_name] = None
                        else:
                            row_data[attr_name] = normalize_cell_content(val)
                            
                        if val is not None:
                            has_any_value = True
                
                # If row is completely empty, skip it
                if not has_any_value:
                    continue
                    
                # Validate title
                title_val = row_data.get("title")
                if title_val is None:
                    warnings.append(f"Row {row_idx} in sheet '{name}' skipped: missing a valid title.")
                    continue
                    
                # Create the BusinessWorkbookRow object
                business_row = BusinessWorkbookRow(
                    sheet_name=name,
                    row_idx=row_idx,
                    id=row_data.get("id"),
                    title=title_val,
                    image_link=row_data.get("image_link"),
                    linkedin_draft=row_data.get("linkedin_draft"),
                    facebook_draft=row_data.get("facebook_draft"),
                    x_draft=row_data.get("x_draft"),
                    instagram_draft=row_data.get("instagram_draft"),
                    pinterest_draft=row_data.get("pinterest_draft"),
                    threads_draft=row_data.get("threads_draft"),
                    tiktok_draft=row_data.get("tiktok_draft"),
                    youtube_draft=row_data.get("youtube_draft"),
                    link_post_raw=row_data.get("link_post_raw"),
                    broken_draft_refs=row_data.get("broken_draft_refs"),
                )
                parsed_rows.append(business_row)
                
    finally:
        wb.close()
        
    return parsed_rows, warnings


def map_news_item_to_business_row(news_item: NewsItem, row_idx: int) -> BusinessWorkbookRow:
    """
    Coexistence Mapper: Maps a Contract A NewsItem row to a Contract B BusinessWorkbookRow.
    This enables Pipeline B posting modules to consume legacy rows uniformly if needed.
    """
    # Try reading the draft content from the external generated post file if available
    draft_content = None
    if news_item.generated_post_file and os.path.exists(news_item.generated_post_file):
        try:
            with open(news_item.generated_post_file, "r", encoding="utf-8") as f:
                draft_content = f.read().strip()
        except Exception:
            pass
            
    # If the file wasn't read, fall back to published_text or snippet
    if not draft_content:
        draft_content = news_item.published_text or news_item.snippet
        
    # Map the draft to the platform specified in NewsItem
    platform_name = (news_item.platform or "linkedin").strip().lower()
    
    linkedin_draft = draft_content if "linkedin" in platform_name else None
    facebook_draft = draft_content if "facebook" in platform_name else None
    x_draft = draft_content if ("x" in platform_name or "twitter" in platform_name) else None
    instagram_draft = draft_content if "instagram" in platform_name else None
    pinterest_draft = draft_content if "pinterest" in platform_name else None
    threads_draft = draft_content if "threads" in platform_name else None
    tiktok_draft = draft_content if "tiktok" in platform_name else None
    youtube_draft = draft_content if "youtube" in platform_name else None
    
    # Establish a default Link Post string
    link_post = None
    if news_item.status == "posted":
        canonical_platform = "LinkedIn"
        if facebook_draft:
            canonical_platform = "Facebook"
        elif x_draft:
            canonical_platform = "X"
        elif instagram_draft:
            canonical_platform = "Instagram"
        elif pinterest_draft:
            canonical_platform = "Pinterest"
        elif threads_draft:
            canonical_platform = "Threads"
        elif tiktok_draft:
            canonical_platform = "TikTok"
        elif youtube_draft:
            canonical_platform = "YouTube"
            
        note_val = news_item.notes or "posted"
        if note_val.startswith("http://") or note_val.startswith("https://"):
            link_post = f"{canonical_platform}: {note_val}"
        else:
            link_post = f"{canonical_platform}: [posted-no-link] {note_val}".strip()
    elif news_item.status == "error":
        link_post = f"LinkedIn: [error] {news_item.notes or 'unknown error'}"
    elif news_item.status == "skipped":
        link_post = f"LinkedIn: [skip] {news_item.notes or 'skipped by operator'}"
        
    return BusinessWorkbookRow(
        sheet_name="Compatibility",
        row_idx=row_idx,
        id=news_item.id,
        title=news_item.title or "Untitled news",
        image_link=news_item.image_file,
        linkedin_draft=linkedin_draft,
        facebook_draft=facebook_draft,
        x_draft=x_draft,
        instagram_draft=instagram_draft,
        pinterest_draft=pinterest_draft,
        threads_draft=threads_draft,
        tiktok_draft=tiktok_draft,
        youtube_draft=youtube_draft,
        link_post_raw=link_post
    )


def get_sheet_name_for_keyword(keyword: str, existing_sheets: List[str]) -> str:
    """
    Map scraped news keywords to sheet names.
    The sheet name should be exactly the keyword, cleaned and truncated to 31 characters.
    """
    kw_clean = keyword.strip()
    # Excel sheet titles are case-insensitive and limited to 31 characters.
    # Check if there is an existing sheet that matches case-insensitively first to preserve original sheet casing.
    for sheet in existing_sheets:
        if sheet.lower() == kw_clean.lower() or (len(kw_clean) > 31 and sheet.lower() == kw_clean[:31].lower()):
            return sheet
            
    if len(kw_clean) > 31:
        kw_clean = kw_clean[:31]
    return kw_clean


def save_news_to_business_excel(items: List[NewsItem], config, limit: Optional[int] = None) -> List[NewsItem]:
    """
    Save scraped news items to the Business Workbook (Contract B) in separate category sheets.
    """
    filepath = config.excel_file
    
    if openpyxl is None:
        print("[ERROR] openpyxl is not installed. Please run pip install -r requirements.txt to install it.")
        return []

    from src.writeback import is_workbook_locked, create_workbook_backup
    
    if os.path.exists(filepath):
        if is_workbook_locked(filepath):
            print(f"[ERROR] Cannot write to Excel workbook. The file '{filepath}' is currently open/locked by another application.")
            return []
        if config.backup_enabled:
            try:
                create_workbook_backup(filepath)
            except Exception as e:
                print(f"[WARNING] Failed to create workbook backup: {e}")
    else:
        # If it doesn't exist, initialize a new workbook with default 'Payment' sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Payment"
        headers = ["#", "Trillion $ news Title", "Image link", "Linkedin", "Facebook", "X (Twitter)", "Instagram", "Pinterest", "Threads", "TikTok", "YouTube", "Link Post"]
        ws.append(headers)
        wb.save(filepath)
        print(f"[SUCCESS] Initialized new Business Workbook at {filepath}")

    wb = openpyxl.load_workbook(filepath)
    saved_items = []
    
    try:
        def slugify(text: str) -> str:
            import re
            text = text.lower()
            text = re.sub(r'[^a-z0-9_]', '_', text)
            text = re.sub(r'_+', '_', text)
            return text.strip('_')
            
        def normalize_title(title: str) -> str:
            if not title:
                return ""
            import re
            t = title.strip().lower()
            t = re.sub(r'[^a-z0-9\s]', '', t)
            return " ".join(t.split())

        saved_counts_per_sheet = {}
        for item in items:
            sheet_name = get_sheet_name_for_keyword(item.keyword or "Payment", wb.sheetnames)
            saved_count = saved_counts_per_sheet.get(sheet_name, 0)
            
            if limit is not None and saved_count >= limit:
                if item.image_file and item.image_file.startswith("temp_"):
                    temp_path = os.path.join(config.image_dir, item.image_file)
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                continue
            
            if sheet_name not in wb.sheetnames:
                ws = wb.create_sheet(title=sheet_name)
                headers = ["#", "Trillion $ news Title", "Image link", "Linkedin", "Facebook", "X (Twitter)", "Instagram", "Pinterest", "Threads", "TikTok", "YouTube", "Link Post"]
                ws.append(headers)
            else:
                ws = wb[sheet_name]
                
            header_row = []
            for r in ws.iter_rows(max_row=1, values_only=True):
                header_row = r
                break
                
            col_map = {}
            for idx, val in enumerate(header_row):
                norm = normalize_header(val)
                if norm:
                    col_map[norm] = idx + 1
                    
            title_col = col_map.get("trillion $ news title", 2)
            existing_normalized_titles = set()
            for r in range(2, ws.max_row + 1):
                cell_val = ws.cell(row=r, column=title_col).value
                if cell_val:
                    existing_normalized_titles.add(normalize_title(str(cell_val)))
                    
            norm_item_title = normalize_title(item.title)
            id_col = col_map.get("#", 1)
            col_img = col_map.get("image link", 3)
            if norm_item_title in existing_normalized_titles:
                backfilled_image = False
                if item.image_file and item.image_file.startswith("temp_"):
                    for r in range(2, ws.max_row + 1):
                        if normalize_title(str(ws.cell(row=r, column=title_col).value)) != norm_item_title:
                            continue
                        existing_img = normalize_cell_content(ws.cell(row=r, column=col_img).value)
                        if existing_img:
                            break
                        row_id_val = ws.cell(row=r, column=id_col).value
                        try:
                            row_id = int(float(row_id_val))
                        except (ValueError, TypeError):
                            row_id = row_id_val or r
                        if not item.found_date:
                            from datetime import datetime
                            item.found_date = datetime.now().strftime("%Y-%m-%d")
                        old_filename = item.image_file
                        old_path = os.path.join(config.image_dir, old_filename)
                        ext = os.path.splitext(old_filename)[1]
                        slug_kw = slugify(sheet_name or item.keyword or "news")
                        padded_id = f"{row_id:03d}" if isinstance(row_id, int) else str(row_id)
                        new_filename = f"{item.found_date}_{padded_id}_{slug_kw}{ext}"
                        new_path = os.path.join(config.image_dir, new_filename)
                        if os.path.exists(old_path):
                            try:
                                os.rename(old_path, new_path)
                                ws.cell(row=r, column=col_img).value = new_filename
                                backfilled_image = True
                                print(f"[INFO] Backfilled image link for existing row in sheet '{sheet_name}': {item.title}")
                            except Exception as e:
                                print(f"[WARNING] Failed to backfill image for existing row: {e}")
                        break
                    if not backfilled_image:
                        temp_path = os.path.join(config.image_dir, item.image_file)
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
                if not backfilled_image:
                    print(f"[INFO] Skipping already saved title in sheet '{sheet_name}': {item.title}")
                continue
            # Find the maximum numeric ID currently in the sheet to ensure contiguous assignment
            max_id = 0
            for r in range(2, ws.max_row + 1):
                val = ws.cell(row=r, column=id_col).value
                if val is not None:
                    try:
                        numeric_id = int(float(val))
                        if numeric_id > max_id:
                            max_id = numeric_id
                    except (ValueError, TypeError):
                        pass
            next_id = max_id + 1
                    
            item.id = next_id
            item.keyword = sheet_name
            if not item.found_date:
                from datetime import datetime
                item.found_date = datetime.now().strftime("%Y-%m-%d")
                
            if item.image_file and item.image_file.startswith("temp_"):
                old_filename = item.image_file
                old_path = os.path.join(config.image_dir, old_filename)
                
                ext = os.path.splitext(old_filename)[1]
                slug_kw = slugify(item.keyword or "news")
                padded_id = f"{item.id:03d}" if isinstance(item.id, int) else str(item.id)
                new_filename = f"{item.found_date}_{padded_id}_{slug_kw}{ext}"
                new_path = os.path.join(config.image_dir, new_filename)
                
                if os.path.exists(old_path):
                    try:
                        os.rename(old_path, new_path)
                        item.image_file = new_filename
                    except Exception as e:
                        print(f"[WARNING] Failed to rename temp screenshot file: {e}")
                else:
                    item.image_file = None
                    
            col_id = id_col
            col_title = col_map.get("trillion $ news title", 2)
            
            new_row_idx = ws.max_row + 1
            ws.cell(row=new_row_idx, column=col_id).value = item.id
            ws.cell(row=new_row_idx, column=col_title).value = item.title
            ws.cell(row=new_row_idx, column=col_img).value = item.image_file
            
            for col_idx in col_map.values():
                if col_idx not in [col_id, col_title, col_img]:
                    ws.cell(row=new_row_idx, column=col_idx).value = None
            
            item.status = "new"
            item.platform = config.default_platform
            saved_items.append(item)
            saved_counts_per_sheet[sheet_name] = saved_count + 1
            
        # Clean up empty placeholder sheets if we have other valid sheets
        placeholder_names = ["sheet", "sheet1", "payment", "charity & tokenization"]
        non_placeholder_sheets = [name for name in wb.sheetnames if name.lower() not in placeholder_names]
        if non_placeholder_sheets:
            for name in list(wb.sheetnames):
                if name.lower() in placeholder_names:
                    ws_check = wb[name]
                    if ws_check.max_row <= 1:
                        wb.remove(ws_check)
                        
        wb.save(filepath)
        if saved_items:
            print(f"[SUCCESS] Appended {len(saved_items)} new articles to Business Workbook sheets.")
    finally:
        wb.close()
        
    return saved_items


def generate_drafts_for_business_excel(config, limit: Optional[int] = None, platform_option: Optional[str] = None, target_ids: Optional[List[int]] = None):
    """
    Check all category sheets in the Business Workbook. Find rows where drafts are missing.
    Generate the missing platform drafts using Gemini and save directly in the Excel cell.
    """
    filepath = config.excel_file
    
    if openpyxl is None:
        print("[ERROR] openpyxl is not installed. Please run pip install -r requirements.txt to install it.")
        sys.exit(1)
        
    if not os.path.exists(filepath):
        print(f"[ERROR] Excel file '{filepath}' does not exist. Please run search first.")
        sys.exit(1)
        
    from src.writeback import is_workbook_locked, create_workbook_backup
    
    if is_workbook_locked(filepath):
        print(f"[ERROR] Workbook '{filepath}' is currently locked/open in another application.")
        sys.exit(1)
        
    if config.backup_enabled:
        try:
            create_workbook_backup(filepath)
        except Exception as e:
            print(f"[WARNING] Failed to create workbook backup: {e}")
            
    from src.ai_writer import generate_ai_post, validate_generated_post
    import sys
    
    wb = openpyxl.load_workbook(filepath)
    try:
        if platform_option and platform_option.lower() != "all":
            p_clean = platform_option.lower().strip()
            if p_clean in ["x", "twitter", "x (twitter)"]:
                target_platforms = ["x"]
            else:
                target_platforms = [p_clean]
        else:
            target_platforms = ["linkedin", "facebook", "x", "instagram", "pinterest", "threads", "tiktok", "youtube"]
            
        rows_processed = 0
        
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            header_row = []
            for row in ws.iter_rows(max_row=1, values_only=True):
                header_row = row
                break
                
            if not header_row or all(cell is None for cell in header_row):
                continue
                
            normalized_headers_set = set(normalize_header(cell_val) for cell_val in header_row if cell_val is not None)
            if "trillion $ news title" not in normalized_headers_set:
                continue
                
            col_map = {}
            for idx, val in enumerate(header_row):
                norm = normalize_header(val)
                if norm:
                    col_map[norm] = idx + 1
                    
            title_col = col_map.get("trillion $ news title")
            if not title_col:
                continue
                
            platform_cols = {}
            for plat_norm, attr in REQUIRED_MAPPING.items():
                if plat_norm == "#" or plat_norm == "trillion $ news title" or plat_norm == "image link":
                    continue
                simp_name = plat_norm
                if plat_norm == "x (twitter)":
                    simp_name = "x"
                if plat_norm in col_map:
                    platform_cols[simp_name] = col_map[plat_norm]
                    
            rows_processed_for_sheet = 0
            for row_idx in range(2, ws.max_row + 1):
                if limit is not None and rows_processed_for_sheet >= limit:
                    break
                    
                # If target_ids is specified, only process matching rows
                id_col_idx = col_map.get("#", 1)
                row_id = ws.cell(row=row_idx, column=id_col_idx).value
                try:
                    row_id_int = int(row_id)
                except (ValueError, TypeError):
                    row_id_int = row_id
                    
                if target_ids is not None:
                    is_match = False
                    for target in target_ids:
                        if isinstance(target, (tuple, list)):
                            if len(target) == 2 and str(target[0]).lower() == str(sheet_name).lower() and target[1] == row_id_int:
                                is_match = True
                                break
                        elif target == row_id_int:
                            is_match = True
                            break
                    if not is_match:
                        continue
                    
                title_val = ws.cell(row=row_idx, column=title_col).value
                title_norm = normalize_cell_content(title_val)
                if not title_norm:
                    continue
                    
                missing_platforms = []
                post_dir = getattr(config, "post_dir", None)
                for p in target_platforms:
                    if p in platform_cols:
                        cell_val = ws.cell(row=row_idx, column=platform_cols[p]).value
                        from src.draft_paths import draft_cell_has_content

                        if not draft_cell_has_content(cell_val, filepath, post_dir):
                            missing_platforms.append(p)
                            
                if not missing_platforms:
                    continue
                    
                generated_any = False
                for p in missing_platforms:
                    print(f"[INFO] Generating {p} draft for Row {row_idx} in sheet '{sheet_name}': '{title_norm}'")
                    try:
                        content = generate_ai_post(
                            title=title_norm,
                            source="",
                            snippet="",
                            url="",
                            platform=p,
                            config=config
                        )
                        
                        # Generate post markdown file under output/posts/
                        id_col_idx = col_map.get("#", 1)
                        id_val = ws.cell(row=row_idx, column=id_col_idx).value
                        try:
                            id_val = int(id_val)
                        except Exception:
                            id_val = row_idx
                            
                        from datetime import datetime
                        found_date = datetime.now().strftime("%Y-%m-%d")
                        image_col_idx = col_map.get("image link", 3)
                        image_val = ws.cell(row=row_idx, column=image_col_idx).value
                        
                        import re
                        if image_val and "_" in image_val:
                            parts = image_val.split("_")
                            if len(parts) >= 1 and re.match(r'^\d{4}-\d{2}-\d{2}$', parts[0]):
                                found_date = parts[0]
                                
                        from src.models import NewsItem
                        from src.post_writer import write_post_file
                        item = NewsItem(
                            id=id_val,
                            found_date=found_date,
                            keyword=sheet_name,
                            title=title_norm,
                            image_file=image_val,
                            platform=p,
                            status="generated"
                        )
                        post_filepath = None
                        try:
                            post_filepath = write_post_file(item, content, config)
                        except Exception as post_write_err:
                            print(f"[WARNING] Failed to write post file: {post_write_err}")
                            
                        # Save the generated post file path in the Excel cell (fallback to content if file writing failed)
                        ws.cell(row=row_idx, column=platform_cols[p]).value = post_filepath or content
                        generated_any = True
                        
                        if not validate_generated_post(content, p):
                            print(f"[WARNING] Generated draft for platform '{p}' failed validation checks.")
                    except Exception as e:
                        print(f"[ERROR] Failed to generate draft for platform '{p}' on row {row_idx}: {e}")
                        
                if generated_any:
                    rows_processed_for_sheet += 1
                    rows_processed += 1
                
        wb.save(filepath)
        print(f"[SUCCESS] Generation complete. Generated drafts for {rows_processed} rows.")
    finally:
        wb.close()


def repair_broken_draft_references(config) -> List[str]:
    """Clear platform draft cells that point to markdown files missing on disk."""
    filepath = config.excel_file
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workbook file '{filepath}' does not exist.")

    from src.writeback import is_workbook_locked
    from src.draft_paths import looks_like_file_reference, resolve_post_draft_path

    if is_workbook_locked(filepath):
        raise PermissionError(
            f"Workbook '{filepath}' is currently locked/open in another application."
        )

    post_dir = getattr(config, "post_dir", None)
    wb = openpyxl.load_workbook(filepath)
    actions: List[str] = []

    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            header_row = []
            for row in ws.iter_rows(max_row=1, values_only=True):
                header_row = row
                break
            if not header_row:
                continue

            col_map = {}
            for idx, val in enumerate(header_row):
                norm = normalize_header(val)
                if norm:
                    col_map[norm] = idx + 1

            platform_cols = {}
            for plat_norm in REQUIRED_MAPPING:
                if plat_norm in ("#", "trillion $ news title", "image link"):
                    continue
                if plat_norm in col_map:
                    platform_cols[plat_norm] = col_map[plat_norm]

            for row_idx in range(2, ws.max_row + 1):
                for plat_norm, col_idx in platform_cols.items():
                    cell_val = ws.cell(row=row_idx, column=col_idx).value
                    cell_str = normalize_cell_content(cell_val)
                    if not cell_str or not looks_like_file_reference(cell_str):
                        continue
                    if resolve_post_draft_path(cell_str, filepath, post_dir):
                        continue
                    ws.cell(row=row_idx, column=col_idx).value = None
                    actions.append(
                        f"Cleared broken {plat_norm} draft reference on Excel row {row_idx} in sheet '{sheet_name}'"
                    )

        if actions:
            wb.save(filepath)
    finally:
        wb.close()

    return actions
