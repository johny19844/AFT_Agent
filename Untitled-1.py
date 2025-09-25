def parse_csv_file(file_path):
    """
    Функция для парсинга CSV файлов с обработкой ошибок.
    Возвращает список словарей (каждая строка - словарь с заголовками как ключами).
    """
    import csv

    data = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        return data
    except FileNotFoundError:
        print(f"Ошибка: Файл '{file_path}' не найден.")
        return None
    except csv.Error as e:
        print(f"Ошибка при чтении CSV файла: {e}")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return None
        # Пример использования функции parse_csv_file
if __name__ == "__main__":
    # Замените 'example.csv' на путь к вашему CSV файлу
    file_path = 'example.csv'
    result = parse_csv_file(file_path)
    if result is not None:
        print("Содержимое CSV файла:")
        for row in result:
            print(row)
        # Если нужно, можно обработать данные дальше
    else:
        print("Не удалось прочитать CSV файл.")
        # Создадим example.csv с тестовыми данными, если файл не существует
        import os
        import csv

        if not os.path.exists('example.csv'):
            with open('example.csv', mode='w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Запишем заголовки
                writer.writerow(['Имя', 'Возраст', 'Город'])
                # Запишем несколько строк данных
                writer.writerow(['Алиса', '30', 'Москва'])
                writer.writerow(['Боб', '25', 'Санкт-Петербург'])
                writer.writerow(['Ева', '28', 'Казань'])
            print("Файл example.csv был создан для тестирования.")
            def sum_numbers(a, b):
                """
                Функция для вычисления суммы двух чисел.
                """
                return a + b
