import csv
import io
from celery import shared_task
from .models import Part

@shared_task
def auto_restock():
    """
    Verifica todas as peças e, se a quantidade estiver abaixo de um limite, reabastece.
    """
    threshold = 70
    restock_amount = 100

    # Filtra as peças que precisam de reposição
    parts_to_restock = Part.objects.filter(quantity__lt=threshold)
    for part in parts_to_restock:
        part.quantity += restock_amount
        part.save()
    return f"Reposto {parts_to_restock.count()} peças."


@shared_task
def import_parts_csv(file_data):
    """
    Processa o conteúdo de um arquivo CSV (como string) e cria peças no banco de dados.
    O CSV deve ter o formato:
    
    part_number, name, details, price, quantity
    XPTO1234, Filtro de Óleo, Filtro de alta qualidade, 45.00, 50
    ABC123, Pastilha de Freio, Conjunto de 4 pastilhas, 120.00, 30
    """
    file_io = io.StringIO(file_data)
    reader = csv.DictReader(file_io)
    count = 0
    for row in reader:
        try:
            part_number = row['part_number']
            name = row['name']
            details = row['details']
            price = float(row['price'])
            quantity = int(row['quantity'])
            Part.objects.create(
                part_number=part_number,
                name=name,
                details=details,
                price=price,
                quantity=quantity
            )
            count += 1
        except Exception as e:
            print(f"Erro ao processar a linha {row}: {e}")
    return f"Importadas {count} peças com sucesso."
