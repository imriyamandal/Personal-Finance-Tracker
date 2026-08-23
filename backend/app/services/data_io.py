import os
import sys
import csv
import pandas as pd
from datetime import datetime

# Ensure database directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database")))
    import db_manager

# Import reportlab components for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ----------------- Export Functions -----------------

def export_to_csv(user_id, output_path):
    """Exports all transactions of a user to a CSV file."""
    conn = db_manager.get_db_connection()
    query = """
    SELECT t.id, t.date, t.amount, t.transaction_type, c.name as category, t.description, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    ORDER BY t.date DESC;
    """
    df = pd.read_sql_query(query, conn, params=[user_id])
    conn.close()
    
    df.to_csv(output_path, index=False)
    return True

def export_to_excel(user_id, output_path):
    """Exports all transactions of a user to an Excel file."""
    conn = db_manager.get_db_connection()
    query = """
    SELECT t.id, t.date, t.amount, t.transaction_type, c.name as category, t.description, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    ORDER BY t.date DESC;
    """
    df = pd.read_sql_query(query, conn, params=[user_id])
    conn.close()
    
    df.to_excel(output_path, index=False, sheet_name="Transactions")
    return True

def export_to_pdf(user_id, output_path):
    """Compiles a professional PDF financial report containing transaction summaries and list."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Summary Stats
    cursor.execute("""
    SELECT 
        SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) as income,
        SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) as expense
    FROM transactions WHERE user_id = ?;
    """, (user_id,))
    totals = cursor.fetchone()
    total_income = totals["income"] if totals and totals["income"] else 0.0
    total_expense = totals["expense"] if totals and totals["expense"] else 0.0
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0
    
    # 2. Fetch Category Breakdown
    cursor.execute("""
    SELECT c.name as category, SUM(t.amount) as spent 
    FROM transactions t
    INNER JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ? AND t.transaction_type = 'Expense'
    GROUP BY t.category_id
    ORDER BY spent DESC;
    """, (user_id,))
    categories = cursor.fetchall()
    
    # 3. Fetch Transactions list (recent 50)
    cursor.execute("""
    SELECT t.date, t.amount, t.transaction_type, c.name as category, t.description, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    ORDER BY t.date DESC
    LIMIT 50;
    """, (user_id,))
    tx_list = cursor.fetchall()
    conn.close()
    
    # 4. Generate PDF flowables
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    
    story = []
    
    # Header block
    story.append(Paragraph("Personal Finance Management Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.today().strftime('%d-%m-%Y')}", body_style))
    story.append(Spacer(1, 15))
    
    # Summary Cards Table
    summary_data = [
        ["Total Income", "Total Expenses", "Net Savings", "Savings Rate"],
        [f"${total_income:,.2f}", f"${total_expense:,.2f}", f"${net_savings:,.2f}", f"{savings_rate:.1f}%"]
    ]
    summary_table = Table(summary_data, colWidths=[130]*4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica'),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#334155')),
        ('BACKGROUND', (0,1), (-1,1), colors.white),
    ]))
    story.append(Paragraph("Financial Executive Summary", section_style))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Category Spending Table
    cat_data = [["Expense Category", "Amount Spent"]]
    for cat in categories:
        cat_data.append([cat["category"], f"${cat['spent']:,.2f}"])
        
    if len(cat_data) > 1:
        cat_table = Table(cat_data, colWidths=[260, 260])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(Paragraph("Expenses by Category", section_style))
        story.append(cat_table)
        story.append(Spacer(1, 15))
        
    # Transaction List Table
    tx_data = [["Date", "Type", "Category", "Amount", "Method", "Description"]]
    for tx in tx_list:
        date_formatted = datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%d-%m-%Y")
        tx_data.append([
            date_formatted,
            tx["transaction_type"],
            tx["category"] or "Other",
            f"${tx['amount']:,.2f}",
            tx["payment_method"],
            tx["description"] or ""
        ])
        
    if len(tx_data) > 1:
        tx_table = Table(tx_data, colWidths=[70, 60, 80, 75, 80, 165])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(Paragraph(f"Recent Transactions (Last {len(tx_data)-1})", section_style))
        story.append(tx_table)
        
    doc.build(story)
    return True

# ----------------- Import Function -----------------

def import_from_file(user_id, file_path):
    """Imports transactions from a CSV or Excel sheet, resolving duplicates and mapping categories."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel sheet.")
        
    # Standardize column header mappings
    column_map = {col.lower().replace("_", "").replace(" ", ""): col for col in df.columns}
    
    req_headers = {
        "date": "Date",
        "amount": "Amount",
        "transactiontype": "transaction_type",
        "category": "Category",
    }
    
    mapped_columns = {}
    for req_key, canonical_name in req_headers.items():
        matched_header = None
        for col_cleaned, orig_header in column_map.items():
            if req_key in col_cleaned or col_cleaned in req_key:
                matched_header = orig_header
                break
        if not matched_header:
            raise ValueError(f"Missing required header match for: {canonical_name}")
        mapped_columns[req_key] = matched_header
        
    # Optional headers
    desc_header = next((orig for cleaned, orig in column_map.items() if "desc" in cleaned), None)
    pay_header = next((orig for cleaned, orig in column_map.items() if "method" in cleaned or "pay" in cleaned), None)
    
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    # Preload categories to map name -> id
    cursor.execute("SELECT id, name, type FROM categories;")
    categories = cursor.fetchall()
    category_map = {(row["name"].lower(), row["type"].lower()): row["id"] for row in categories}
    
    imported_count = 0
    duplicate_count = 0
    errors_count = 0
    
    for idx, row in df.iterrows():
        # Parse Amount
        try:
            amount = float(row[mapped_columns["amount"]])
            if amount <= 0:
                errors_count += 1
                continue
        except (ValueError, TypeError):
            errors_count += 1
            continue
            
        # Parse Type
        tx_type_raw = str(row[mapped_columns["transactiontype"]]).strip().capitalize()
        if tx_type_raw in ["Income", "Expense"]:
            tx_type = tx_type_raw
        elif "inc" in tx_type_raw.lower():
            tx_type = "Income"
        elif "exp" in tx_type_raw.lower():
            tx_type = "Expense"
        else:
            errors_count += 1
            continue
            
        # Parse Date
        date_raw = str(row[mapped_columns["date"]]).strip()
        db_date = None
        for date_fmt in ["%d-%m-%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                # Remove timestamps if present in date cell
                date_cleaned = date_raw.split(" ")[0]
                db_date = datetime.strptime(date_cleaned, date_fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
        if not db_date:
            errors_count += 1
            continue
            
        # Category Mapping
        cat_name_raw = str(row[mapped_columns["category"]]).strip()
        cat_key = (cat_name_raw.lower(), tx_type.lower())
        cat_id = category_map.get(cat_key)
        
        if not cat_id:
            # Create a new custom category for this user
            try:
                cursor.execute("""
                INSERT INTO categories (user_id, name, type, is_default)
                VALUES (?, ?, ?, 0);
                """, (user_id, cat_name_raw, tx_type))
                conn.commit()
                cat_id = cursor.lastrowid
                category_map[cat_key] = cat_id
            except Exception:
                # Fallback to Other
                fallback_name = "Other" if tx_type == "Expense" else "Other Income"
                cat_id = category_map.get((fallback_name.lower(), tx_type.lower()))
                
        # Description
        description = ""
        if desc_header:
            description = str(row[desc_header]).strip()
            if description.lower() == 'nan':
                description = ""
                
        # Payment Method
        payment_method = "Other"
        if pay_header:
            pay_raw = str(row[pay_header]).strip().title()
            if pay_raw in ["Cash", "Card", "Bank Transfer", "UPI", "Other"]:
                payment_method = pay_raw
                
        # Deduplication Check
        cursor.execute("""
        SELECT id FROM transactions
        WHERE user_id = ? AND amount = ? AND transaction_type = ? AND category_id = ? 
          AND description = ? AND date = ? AND payment_method = ?;
        """, (user_id, amount, tx_type, cat_id, description, db_date, payment_method))
        
        if cursor.fetchone():
            duplicate_count += 1
            continue
            
        # Write transaction
        cursor.execute("""
        INSERT INTO transactions (user_id, amount, transaction_type, category_id, description, date, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (user_id, amount, tx_type, cat_id, description, db_date, payment_method))
        imported_count += 1
        
    conn.commit()
    conn.close()
    
    return {
        "imported": imported_count,
        "duplicates_skipped": duplicate_count,
        "errors_skipped": errors_count
    }
