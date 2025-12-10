#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Route:
    """Датакласс для представления туристического маршрута."""

    name: str
    distance: float
    difficulty: str


@dataclass
class RouteContainer:
    """Контейнер для управления коллекцией маршрутов."""

    routes: List[Route] = field(default_factory=list)
    _current_file: Optional[str] = field(default=None, init=False)

    def add_route(self, name: str, distance: float, difficulty: str) -> None:
        """Добавляет новый маршрут в коллекцию."""
        if difficulty not in ["легкий", "средний", "сложный"]:
            raise ValueError("Сложность должна быть 'легкий', 'средний' или 'сложный'")

        self.routes.append(Route(name=name, distance=distance, difficulty=difficulty))

    def display_all(self) -> str:
        """Возвращает форматированное представление всех маршрутов."""
        if not self.routes:
            return "Нет сохраненных маршрутов."

        # Сортируем маршруты по названию
        sorted_routes = sorted(self.routes, key=lambda route: route.name)

        table: List[str] = []
        # Шапка таблицы
        header_line = "+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10)
        table.append(header_line)
        table.append(
            "| {:^4} | {:^30} | {:^12} | {:^10} |".format(
                "№", "Название маршрута", "Расстояние (км)", "Сложность"
            )
        )
        table.append(header_line)

        # Данные маршрутов
        for idx, route in enumerate(sorted_routes, 1):
            table.append(
                "| {:^4} | {:<30} | {:^12.1f} | {:^10} |".format(
                    idx, route.name, route.distance, route.difficulty
                )
            )

        table.append(header_line)
        return "\n".join(table)

    def select_by_distance(self, min_distance: float) -> List[Route]:
        """Выбирает маршруты длиннее заданного расстояния."""
        result: List[Route] = []
        for route in self.routes:
            if route.distance > min_distance:
                result.append(route)
        return result

    def load_from_xml(self, filename: str) -> None:
        """Загружает маршруты из XML файла."""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()

            # Очищаем текущую коллекцию
            self.routes = []

            for route_elem in root.findall("route"):
                name_elem = route_elem.find("name")
                distance_elem = route_elem.find("distance")
                difficulty_elem = route_elem.find("difficulty")

                if (
                    name_elem is not None
                    and name_elem.text is not None
                    and distance_elem is not None
                    and distance_elem.text is not None
                    and difficulty_elem is not None
                    and difficulty_elem.text is not None
                ):
                    name = name_elem.text.strip()
                    try:
                        distance = float(distance_elem.text)
                    except ValueError:
                        raise ValueError(
                            f"Некорректное значение расстояния: {distance_elem.text}"
                        )
                    difficulty = difficulty_elem.text.strip()

                    self.routes.append(
                        Route(name=name, distance=distance, difficulty=difficulty)
                    )

            self._current_file = filename

        except FileNotFoundError:
            raise FileNotFoundError(f"Файл '{filename}' не найден.")
        except ET.ParseError:
            raise ET.ParseError(f"Некорректный формат XML в файле '{filename}'.")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке файла: {e}")

    def save_to_xml(self, filename: Optional[str] = None) -> str:
        """Сохраняет маршруты в XML файл и возвращает имя сохраненного файла."""
        if not self.routes:
            raise ValueError("Нет маршрутов для сохранения.")

        # Если имя файла не указано, используем текущий или стандартное имя
        if filename is None:
            if self._current_file:
                filename = self._current_file
            else:
                filename = "routes.xml"

        root = ET.Element("routes")

        for route in self.routes:
            route_elem = ET.Element("route")

            name_elem = ET.SubElement(route_elem, "name")
            name_elem.text = route.name

            distance_elem = ET.SubElement(route_elem, "distance")
            distance_elem.text = str(route.distance)

            difficulty_elem = ET.SubElement(route_elem, "difficulty")
            difficulty_elem.text = route.difficulty

            root.append(route_elem)

        tree = ET.ElementTree(root)

        # Добавляем отступы для читаемости XML
        self._indent(root)

        try:
            tree.write(str(filename), encoding="utf-8", xml_declaration=True)
            self._current_file = filename
            return filename
        except Exception as e:
            raise Exception(f"Ошибка при сохранении файла: {e}")

    def _indent(self, elem: ET.Element, level: int = 0) -> None:
        """Вспомогательная функция для форматирования XML с отступами."""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def get_route_count(self) -> int:
        """Возвращает количество маршрутов."""
        return len(self.routes)

    def clear_routes(self) -> None:
        """Очищает все маршруты."""
        self.routes = []
        self._current_file = None

    def get_total_distance(self) -> float:
        """Возвращает общее расстояние всех маршрутов."""
        return sum(route.distance for route in self.routes)


def build_cli_parser() -> argparse.ArgumentParser:
    """Создает и настраивает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Система управления туристическими маршрутами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s add --name "Горный поход на Эльбрус" --distance 42.5 --difficulty сложный --save
  %(prog)s list
  %(prog)s select --min-distance 20
  %(prog)s load маршруты.xml
  %(prog)s save маршруты.xml
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="доступные команды",
        description="Для получения справки по команде используйте: %(prog)s КОМАНДА --help",
        required=True,
    )

    # Команда добавления маршрута
    add_parser = subparsers.add_parser(
        "add", help="Добавить новый туристический маршрут"
    )
    add_parser.add_argument("--name", required=True, type=str, help="Название маршрута")
    add_parser.add_argument(
        "--distance", required=True, type=float, help="Расстояние маршрута в километрах"
    )
    add_parser.add_argument(
        "--difficulty",
        required=True,
        type=str,
        choices=["легкий", "средний", "сложный"],
        help="Сложность маршрута (легкий, средний, сложный)",
    )
    add_parser.add_argument(
        "--save",
        action="store_true",
        help="Автоматически сохранить после добавления (в routes.xml)",
    )
    add_parser.add_argument(
        "--save-to", type=str, help="Сохранить в указанный файл после добавления"
    )

    # Команда вывода всех маршрутов
    list_parser = subparsers.add_parser(
        "list", help="Показать все сохраненные маршруты"
    )
    list_parser.add_argument(
        "--from-file",
        type=str,
        help="Загрузить маршруты из указанного файла перед показом",
    )

    # Команда выбора маршрутов по расстоянию
    select_parser = subparsers.add_parser(
        "select", help="Выбрать маршруты длиннее заданного расстояния"
    )
    select_parser.add_argument(
        "--min-distance",
        required=True,
        type=float,
        help="Минимальное расстояние (маршруты длиннее этого значения)",
    )
    select_parser.add_argument(
        "--from-file",
        type=str,
        help="Загрузить маршруты из указанного файла перед выборкой",
    )

    # Команда загрузки из XML
    load_parser = subparsers.add_parser("load", help="Загрузить маршруты из XML файла")
    load_parser.add_argument("filename", type=str, help="Имя XML файла для загрузки")

    # Команда сохранения в XML
    save_parser = subparsers.add_parser("save", help="Сохранить маршруты в XML файл")
    save_parser.add_argument(
        "filename",
        type=str,
        nargs="?",
        default=None,
        help="Имя XML файла для сохранения (по умолчанию: routes.xml)",
    )

    return parser


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
            try:
                container.load_from_xml(args.from_file)
                print(f"Данные загружены из: {args.from_file}\n")
            except Exception as e:
                print(f"Ошибка при загрузке: {e}")
                sys.exit(1)

        print(container.display_all())

    elif args.command == "select":
        # Загружаем из файла, если указано
        if hasattr(args, "from_file") and args.from_file:
            try:
                container.load_from_xml(args.from_file)
                print(f"Данные загружены из: {args.from_file}\n")
            except Exception as e:
                print(f"Ошибка при загрузке: {e}")
                sys.exit(1)

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
        try:
            container.load_from_xml(args.filename)
            print(f"✓ Маршруты успешно загружены из файла '{args.filename}'")
            print(f"  Загружено маршрутов: {len(container.routes)}")
        except Exception as e:
            print(f"Ошибка: {e}")
            sys.exit(1)

    elif args.command == "save":
        if not container.routes:
            # Попробуем загрузить из стандартного файла
            if os.path.exists("routes.xml"):
                try:
                    container.load_from_xml("routes.xml")
                    print("Автоматически загружены данные из routes.xml")
                except Exception as e:
                    print(f"Ошибка при загрузке: {e}")
                    sys.exit(1)
            else:
                print("Ошибка: Нет маршрутов для сохранения.")
                print(
                    "Сначала добавьте маршруты с помощью команды 'add' или загрузите из файла."
                )
                sys.exit(1)

        try:
            saved_file = container.save_to_xml(args.filename)
            print(f"✓ Маршруты успешно сохранены в файл '{saved_file}'")
            print(f"  Сохранено маршрутов: {len(container.routes)}")
        except Exception as e:
            print(f"Ошибка: {e}")
            sys.exit(1)

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
