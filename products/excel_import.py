"""
Excel import service for products.
Parses uploaded .xlsx/.xls files, validates rows, and imports into the Product model.
Uses column mapping so Excel headers can differ from database field names.
"""

import pandas as pd
from decimal import Decimal, InvalidOperation
from django.db import transaction

from .models import Product


# Map possible Excel column names to Product model fields.
# Keys are lowercase Excel header variants; value is the model field name.
EXCEL_TO_MODEL_COLUMNS = {
    "product": "name",
    "item": "name",
    "name": "name",
    "cost": "cost_price",
    "price": "cost_price",
    "cost_price": "cost_price",
    "selling": "selling_price",
    "selling_price": "selling_price",
    "quantity": "quantity_in_stock",
    "stock": "quantity_in_stock",
    "quantity_in_stock": "quantity_in_stock",
    "details": "description_ignored",
    "description": "description_ignored",
    "category": "category",
    "low_stock_threshold": "low_stock_threshold",
    "threshold": "low_stock_threshold",
    "supplier": "supplier_name",
    "supplier_name": "supplier_name",
}

# Model fields that are required for each row (logical: product, price, stock).
REQUIRED_MAPPED_FIELDS = {"name", "cost_price", "quantity_in_stock"}

# Defaults when Excel column is missing
DEFAULT_CATEGORY = "Uncategorized"
DEFAULT_LOW_STOCK_THRESHOLD = 10
BATCH_SIZE = 1000


def _normalize_header(h):
    """Normalize Excel header for lookup: strip and lowercase."""
    if pd.isna(h):
        return ""
    return str(h).strip().lower()


def _get_mapped_columns(headers):
    """
    Build mapping from DataFrame column index/name to model field.
    Returns dict: { df_column_name -> model_field_name },
    and set of required model fields that are missing.
    """
    normalized = {_normalize_header(h): h for h in headers}
    mapped = {}
    missing_required = set(REQUIRED_MAPPED_FIELDS)

    for excel_lower, model_field in EXCEL_TO_MODEL_COLUMNS.items():
        if not excel_lower or model_field == "description_ignored":
            continue
        if excel_lower in normalized:
            df_col = normalized[excel_lower]
            mapped[df_col] = model_field
            missing_required.discard(model_field)

    return mapped, missing_required


def _safe_decimal(value, default=None):
    """Convert value to Decimal; return default if invalid."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _safe_int(value, default=None):
    """Convert value to int; return default if invalid."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _validate_and_build_row(row, row_index, col_map):
    """
    Validate one row and return (product_kwargs_dict, error_message).
    If error_message is not None, the row should be skipped.
    """
    data = {}
    for df_col, model_field in col_map.items():
        if model_field == "description_ignored":
            continue
        raw = row.get(df_col)
        if model_field == "name":
            val = raw if pd.isna(raw) else str(raw).strip()
            if not val:
                return None, "Product name is required"
            if len(val) > 200:
                return None, f"Product name too long (max 200 characters), got {len(val)}"
            data["name"] = val
        elif model_field == "category":
            val = raw if pd.isna(raw) else str(raw).strip()
            if not val:
                val = DEFAULT_CATEGORY
            if len(val) > 100:
                return None, f"Category too long (max 100 characters), got {len(val)}"
            data["category"] = val
        elif model_field == "cost_price":
            dec = _safe_decimal(raw)
            if dec is None:
                return None, "Cost price must be a valid number"
            if dec < 1:
                return None, f"Cost price must be at least 1, got {dec}"
            data["cost_price"] = dec
        elif model_field == "selling_price":
            dec = _safe_decimal(raw)
            if dec is not None:
                if dec < 1:
                    return None, f"Selling price must be at least 1, got {dec}"
                data["selling_price"] = dec
            else:
                # Use cost_price if selling_price missing or invalid; set later
                data["selling_price"] = None
        elif model_field == "quantity_in_stock":
            n = _safe_int(raw)
            if n is None:
                return None, "Stock quantity must be a valid number"
            if n < 0:
                return None, f"Stock quantity must be non-negative, got {n}"
            data["quantity_in_stock"] = n
        elif model_field == "low_stock_threshold":
            n = _safe_int(raw)
            if n is not None and n >= 0:
                data["low_stock_threshold"] = n
            else:
                data["low_stock_threshold"] = DEFAULT_LOW_STOCK_THRESHOLD
        elif model_field == "supplier_name":
            val = raw if pd.isna(raw) else str(raw).strip()
            if val:
                if len(val) > 200:
                    return None, f"Supplier name too long (max 200 characters), got {len(val)}"
                data["supplier_name"] = val
            else:
                data["supplier_name"] = None

    # Set defaults for missing fields
    if "selling_price" not in data or data["selling_price"] is None:
        data["selling_price"] = data.get("cost_price", Decimal("1"))
    if "low_stock_threshold" not in data:
        data["low_stock_threshold"] = DEFAULT_LOW_STOCK_THRESHOLD
    if "category" not in data:
        data["category"] = DEFAULT_CATEGORY

    return data, None


def process_excel_upload(file):
    """
    Process an uploaded Excel file and import/update products.

    Args:
        file: File-like object (e.g. request.FILES['file'])

    Returns:
        dict with keys: imported (int), skipped (int), errors (list of {row, error})
    """
    result = {"imported": 0, "skipped": 0, "errors": []}

    try:
        df = pd.read_excel(file, engine="openpyxl")
    except Exception as e:
        result["errors"].append({"row": 0, "error": f"Invalid Excel file: {str(e)}"})
        return result

    if df.empty or len(df.columns) == 0:
        result["errors"].append({"row": 0, "error": "File has no columns"})
        return result

    headers = list(df.columns)
    col_map, missing_required = _get_mapped_columns(headers)
    if missing_required:
        result["errors"].append({
            "row": 0,
            "error": "Missing required columns. Required (or mapped): product/name, price/cost, stock/quantity.",
        })
        return result

    # 1-based row numbers for user-facing error reporting
    to_create = []
    to_update_by_name = {}  # name -> dict of field updates
    seen_names_in_file = set()

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # Excel row (1=header)
        data, err = _validate_and_build_row(row, row_num, col_map)
        if err:
            result["skipped"] += 1
            result["errors"].append({"row": row_num, "error": err})
            continue
        name = data["name"]
        if name in seen_names_in_file:
            result["skipped"] += 1
            result["errors"].append({"row": row_num, "error": "Duplicate product name in file"})
            continue
        seen_names_in_file.add(name)
        to_update_by_name[name] = data

    # Resolve which are creates vs updates
    existing = {p.name: p for p in Product.objects.filter(name__in=to_update_by_name).only("id", "name")}
    update_list = []  # list of (Product, data)
    for name, data in to_update_by_name.items():
        if name in existing:
            update_list.append((existing[name], data))
        else:
            to_create.append(Product(**data))

    with transaction.atomic():
        # Validate for potential database constraint violations before bulk operations
        existing_names = set(Product.objects.filter(name__in=seen_names_in_file).values_list('name', flat=True))
        
        # Separate creates and updates to avoid conflicts
        final_to_create = []
        for product in to_create:
            if product.name not in existing_names:
                final_to_create.append(product)
            else:
                result["skipped"] += 1
                result["errors"].append({"row": 0, "error": f"Product '{product.name}' already exists and would conflict"})
        
        # Handle updates with detailed error reporting
        for product, data in update_list:
            try:
                for key, value in data.items():
                    setattr(product, key, value)
                product.save()
            except Exception as e:
                result["skipped"] += 1
                # Get more detailed error information
                error_msg = str(e)
                if "UNIQUE constraint failed" in error_msg:
                    result["errors"].append({"row": 0, "error": f"Product '{product.name}' violates unique constraint: {error_msg}"})
                elif "CHECK constraint failed" in error_msg:
                    result["errors"].append({"row": 0, "error": f"Product '{product.name}' violates data constraint: {error_msg}"})
                else:
                    result["errors"].append({"row": 0, "error": f"Failed to update product '{product.name}': {error_msg}"})
                continue
        
        # Handle creates with detailed error reporting
        if final_to_create:
            try:
                Product.objects.bulk_create(final_to_create, batch_size=BATCH_SIZE)
            except Exception as e:
                result["skipped"] += len(final_to_create)
                error_msg = str(e)
                if "UNIQUE constraint failed" in error_msg:
                    result["errors"].append({"row": 0, "error": f"Products violate unique constraint: {error_msg}"})
                elif "CHECK constraint failed" in error_msg:
                    result["errors"].append({"row": 0, "error": f"Products violate data constraint: {error_msg}"})
                else:
                    result["errors"].append({"row": 0, "error": f"Failed to create products: {error_msg}"})
        
        result["imported"] = len([p for p in final_to_create]) + len([p for p, d in update_list])

    return result
