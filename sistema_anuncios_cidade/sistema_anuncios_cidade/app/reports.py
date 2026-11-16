import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from sqlalchemy import extract
from reportlab.lib.styles import getSampleStyleSheet
from .models import Sale

def build_monthly_pdf():
    now = datetime.now()
    first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_month = first_day
    start_month = (first_day.replace(day=1) - __import__("datetime").timedelta(days=1)).replace(day=1)
    sales = Sale.query.filter(Sale.sold_at >= start_month, Sale.sold_at < end_month).order_by(Sale.sold_at.asc()).all()
    folder = os.path.join(os.path.dirname(__file__), "..", "instance", "reports")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"relatorio-vendas-{start_month:%Y-%m}.pdf")
    doc = SimpleDocTemplate(path, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Relatório de vendas — {start_month:%m/%Y}", styles["Title"]), Spacer(1, 16)]
    data = [["Produto", "Categoria", "Vendedor", "Comprador", "Preço", "Data", "Horário"]]
    for sale in sales:
        data.append([sale.ad_title, sale.category_name, sale.seller_name, sale.buyer_name or "Não informado",
                     f"R$ {sale.price}", sale.sold_at.strftime("%d/%m/%Y"), sale.sold_at.strftime("%H:%M")])
    if len(data) == 1:
        data.append(["Nenhuma venda registrada neste mês.", "", "", "", "", "", ""])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#233047")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), .4, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("PADDING", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    return path
