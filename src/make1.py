import os
import sys

from task_package.zad1 import RouteContainer, build_cli_parser


def main() -> None:
    """Основная функция приложения."""
    parser = build_cli_parser()
    args = parser.parse_args()

    # Создаем контейнер для маршрутов
    container = RouteContainer()

    # Обработка команд
    if args.command == "add":
        try:
            container.add_route(args.name, args.distance, args.difficulty)
            print(f"✓ Маршрут '{args.name}' успешно добавлен.")
            print(f"  Расстояние: {args.distance} км")
            print(f"  Сложность: {args.difficulty}")

            # Автоматическое сохранение при указании флага
            if args.save:
                saved_file = container.save_to_xml()
                print(f"✓ Данные автоматически сохранены в файл: {saved_file}")
            elif args.save_to:
                saved_file = container.save_to_xml(args.save_to)
                print(f"✓ Данные автоматически сохранены в файл: {saved_file}")
            else:
                print(
                    "⚠  Данные не сохранены. Используйте --save или --save-to для сохранения."
                )

        except ValueError as e:
            print(f"Ошибка: {e}")
            sys.exit(1)

    elif args.command == "list":
        # Загружаем из файла, если указано
        if hasattr(args, "from_file") and args.from_file:
            container.load_from_xml(args.from_file)
            print(f"Данные загружены из: {args.from_file}\n")

        print(container.display_all())

    elif args.command == "select":
        # Загружаем из файла, если указано
        if hasattr(args, "from_file") and args.from_file:
            container.load_from_xml(args.from_file)
            print(f"Данные загружены из: {args.from_file}\n")

        selected_routes = container.select_by_distance(args.min_distance)

        if selected_routes:
            print(f"Маршруты длиннее {args.min_distance} км:\n")
            print("+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10))
            print(
                "| {:^4} | {:^30} | {:^12} | {:^10} |".format(
                    "№", "Название", "Расстояние", "Сложность"
                )
            )
            print("+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10))

            for idx, route in enumerate(selected_routes, 1):
                print(
                    "| {:^4} | {:<30} | {:^12.1f} | {:^10} |".format(
                        idx, route.name, route.distance, route.difficulty
                    )
                )
            print("+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10))

            print(f"\nНайдено маршрутов: {len(selected_routes)}")
        else:
            print(f"Маршруты длиннее {args.min_distance} км не найдены.")

    elif args.command == "load":
        container.load_from_xml(args.filename)
        print(f"✓ Маршруты успешно загружены из файла '{args.filename}'")
        print(f"  Загружено маршрутов: {len(container.routes)}")

    elif args.command == "save":
        if not container.routes:
            # Попробуем загрузить из стандартного файла
            if os.path.exists("routes.xml"):
                container.load_from_xml("routes.xml")
                print("Автоматически загружены данные из routes.xml")
            else:
                print("Ошибка: Нет маршрутов для сохранения.")
                print(
                    "Сначала добавьте маршруты с помощью команды 'add' или загрузите из файла."
                )
                sys.exit(1)

        saved_file = container.save_to_xml(args.filename)
        print(f"✓ Маршруты успешно сохранены в файл '{saved_file}'")
        print(f"  Сохранено маршрутов: {len(container.routes)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        sys.exit(1)
