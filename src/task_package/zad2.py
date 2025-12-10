#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import click


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
    _filename: str = field(default="routes.xml", init=False)

    def add_route(
        self, name: str, distance: float, difficulty: str, auto_save: bool = True
    ) -> None:
        """Добавляет новый маршрут в коллекцию."""
        if difficulty not in ["легкий", "средний", "сложный"]:
            raise ValueError("Сложность должна быть 'легкий', 'средний' или 'сложный'")

        self.routes.append(Route(name=name, distance=distance, difficulty=difficulty))

        # Автоматически сохраняем при добавлении
        if auto_save and self._filename:
            try:
                self.save_to_xml(self._filename)
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                print(f"Предупреждение: не удалось сохранить файл: {e}")

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
        if not os.path.exists(filename):
            # Если файл не существует, создаем пустой список
            self.routes = []
            self._filename = filename
            return

        try:
            tree = ET.parse(filename)
            root = tree.getroot()

            # Очищаем текущую коллекцию
            self.routes = []

            for route_elem in root.findall("route"):
                name_elem = route_elem.find("name")
                distance_elem = route_elem.find("distance")
                difficulty_elem = route_elem.find("difficulty")

                # Проверяем наличие всех элементов
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

                    # Проверяем корректность сложности
                    if difficulty not in ["легкий", "средний", "сложный"]:
                        raise ValueError(f"Некорректная сложность: {difficulty}")

                    self.routes.append(
                        Route(name=name, distance=distance, difficulty=difficulty)
                    )

            # Сохраняем имя файла для автоматического сохранения
            self._filename = filename

        except ET.ParseError:
            raise ValueError(f"Некорректный формат XML в файле '{filename}'.")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке файла: {e}")

    def save_to_xml(self, filename: str) -> None:
        """Сохраняет маршруты в XML файл."""
        if not self.routes:
            raise ValueError("Нет маршрутов для сохранения.")

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
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            # Сохраняем имя файла для последующего использования
            self._filename = filename
        except Exception as e:
            raise Exception(f"Ошибка при сохранении файла: {e}")

    def save_to_json(self, filename: str) -> None:
        """Сохраняет маршруты в JSON файл (дополнительная функция)."""
        if not self.routes:
            raise ValueError("Нет маршрутов для сохранения.")

        try:
            # Преобразуем датаклассы в словари
            routes_data: List[Dict[str, Any]] = []
            for route in self.routes:
                routes_data.append(
                    {
                        "name": route.name,
                        "distance": route.distance,
                        "difficulty": route.difficulty,
                    }
                )

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(routes_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"Ошибка при сохранении в JSON: {e}")

    def load_from_json(self, filename: str) -> None:
        """Загружает маршруты из JSON файла (дополнительная функция)."""
        if not os.path.exists(filename):
            self.routes = []
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                routes_data = json.load(f)

            if not isinstance(routes_data, list):
                raise ValueError("Некорректный формат JSON: ожидается список")

            self.routes = []
            for route_data in routes_data:
                if not isinstance(route_data, dict):
                    raise ValueError("Некорректный формат JSON: ожидается словарь")

                name = route_data.get("name")
                distance = route_data.get("distance")
                difficulty = route_data.get("difficulty")

                if not name or not isinstance(name, str):
                    raise ValueError("Некорректное или отсутствующее имя маршрута")

                if not isinstance(distance, (int, float)):
                    raise ValueError("Некорректное или отсутствующее расстояние")

                if not difficulty or not isinstance(difficulty, str):
                    raise ValueError("Некорректная или отсутствующая сложность")

                if difficulty not in ["легкий", "средний", "сложный"]:
                    raise ValueError(f"Некорректная сложность: {difficulty}")

                self.routes.append(
                    Route(
                        name=str(name),
                        distance=float(distance),
                        difficulty=str(difficulty),
                    )
                )

        except json.JSONDecodeError:
            raise ValueError(f"Некорректный формат JSON в файле '{filename}'.")
        except Exception as e:
            raise Exception(f"Ошибка при загрузке JSON файла: {e}")

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

    def get_total_distance(self) -> float:
        """Возвращает общее расстояние всех маршрутов."""
        return sum(route.distance for route in self.routes)

    def get_difficulty_stats(self) -> Dict[str, int]:
        """Возвращает статистику по сложности маршрутов."""
        stats: Dict[str, int] = {}
        for route in self.routes:
            stats[route.difficulty] = stats.get(route.difficulty, 0) + 1
        return stats

    def search_by_name(self, name: str, exact: bool = False) -> List[Route]:
        """Ищет маршруты по названию."""
        if exact:
            return [r for r in self.routes if r.name.lower() == name.lower()]
        else:
            return [r for r in self.routes if name.lower() in r.name.lower()]


# Глобальный контейнер с автозагрузкой
DEFAULT_FILENAME = "routes.xml"
container = RouteContainer()

# Пытаемся загрузить данные при запуске
try:
    container.load_from_xml(DEFAULT_FILENAME)
except Exception:
    # Если файла нет, создаем пустой контейнер
    container.routes = []


@click.group()
@click.option(
    "--data-file",
    default=DEFAULT_FILENAME,
    help=f"Файл для хранения данных (по умолчанию: {DEFAULT_FILENAME})",
)
@click.pass_context
def cli(ctx: click.Context, data_file: str) -> None:
    """Система управления туристическими маршрутами."""
    # Сохраняем имя файла в контексте
    ctx.obj = {"data_file": data_file}

    # Загружаем данные из указанного файла
    try:
        container.load_from_xml(data_file)
    except Exception:
        container.routes = []


@cli.command()
@click.option(
    "--name", required=True, prompt="Название маршрута", help="Название маршрута"
)
@click.option(
    "--distance",
    required=True,
    type=float,
    prompt="Расстояние (км)",
    help="Расстояние маршрута в километрах",
)
@click.option(
    "--difficulty",
    required=True,
    type=click.Choice(["легкий", "средний", "сложный"]),
    prompt="Сложность (легкий/средний/сложный)",
    help="Сложность маршрута",
)
@click.option("--no-save", is_flag=True, help="Не сохранять автоматически")
@click.pass_context
def add(
    ctx: click.Context, name: str, distance: float, difficulty: str, no_save: bool
) -> None:
    """Добавить новый туристический маршрут."""
    try:
        auto_save = not no_save
        container.add_route(name, distance, difficulty, auto_save=auto_save)

        if auto_save:
            data_file = ctx.obj["data_file"]
            click.echo(
                click.style(
                    f"✓ Маршрут '{name}' добавлен и сохранен в {data_file}", fg="green"
                )
            )
        else:
            click.echo(
                click.style(f"✓ Маршрут '{name}' добавлен (не сохранен)", fg="yellow")
            )
            click.echo(
                click.style("  Используйте команду 'save' для сохранения", fg="yellow")
            )

        click.echo(f"  Расстояние: {distance} км")
        click.echo(f"  Сложность: {difficulty}")
    except ValueError as e:
        click.echo(click.style(f"Ошибка: {e}", fg="red"), err=True)


@cli.command()
@click.pass_context
def list(ctx: click.Context) -> None:
    """Показать все сохраненные маршруты."""
    click.echo(container.display_all())
    click.echo(f"\nВсего маршрутов: {len(container.routes)}")


@cli.command()
@click.option(
    "--min-distance",
    required=True,
    type=float,
    prompt="Минимальное расстояние (км)",
    help="Минимальное расстояние (маршруты длиннее этого значения)",
)
def select(min_distance: float) -> None:
    """Выбрать маршруты длиннее заданного расстояния."""
    selected_routes = container.select_by_distance(min_distance)

    if selected_routes:
        click.echo(f"Маршруты длиннее {min_distance} км:\n")
        click.echo("+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10))
        click.echo(
            "| {:^4} | {:^30} | {:^12} | {:^10} |".format(
                "№", "Название", "Расстояние", "Сложность"
            )
        )
        click.echo("+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10))

        for idx, route in enumerate(selected_routes, 1):
            click.echo(
                "| {:^4} | {:<30} | {:^12.1f} | {:^10} |".format(
                    idx, route.name, route.distance, route.difficulty
                )
            )
        click.echo("+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 12, "-" * 10))

        click.echo(f"\nНайдено маршрутов: {len(selected_routes)}")
    else:
        click.echo(
            click.style(f"Маршруты длиннее {min_distance} км не найдены.", fg="yellow")
        )


@cli.command()
@click.argument("filename", type=click.Path(), required=False)
@click.pass_context
def load(ctx: click.Context, filename: Optional[str]) -> None:
    """Загрузить маршруты из XML файла."""
    if not filename:
        filename = ctx.obj["data_file"]

    try:
        container.load_from_xml(str(filename))
        ctx.obj["data_file"] = filename
        click.echo(
            click.style(f"✓ Маршруты загружены из файла '{filename}'", fg="green")
        )
        click.echo(f"  Загружено маршрутов: {len(container.routes)}")
    except Exception as e:
        click.echo(click.style(f"Ошибка: {e}", fg="red"), err=True)


@cli.command()
@click.argument("filename", type=click.Path(), required=False)
@click.pass_context
def save(ctx: click.Context, filename: Optional[str]) -> None:
    """Сохранить маршруты в XML файл."""
    if not filename:
        filename = ctx.obj["data_file"]

    try:
        container.save_to_xml(str(filename))
        ctx.obj["data_file"] = filename
        click.echo(click.style(f"✓ Маршруты сохранены в файл '{filename}'", fg="green"))
        click.echo(f"  Сохранено маршрутов: {len(container.routes)}")
    except Exception as e:
        click.echo(click.style(f"Ошибка: {e}", fg="red"), err=True)


@cli.command()
@click.argument("xml_file", type=click.Path(exists=True))
@click.argument("json_file", type=click.Path())
def convert(xml_file: str, json_file: str) -> None:
    """Конвертировать маршруты из XML в JSON."""
    try:
        temp_container = RouteContainer()
        temp_container.load_from_xml(xml_file)
        temp_container.save_to_json(json_file)
        click.echo(click.style("✓ Конвертация завершена", fg="green"))
        click.echo(f"  Из: {xml_file}")
        click.echo(f"  В: {json_file}")
        click.echo(f"  Конвертировано маршрутов: {len(temp_container.routes)}")
    except Exception as e:
        click.echo(click.style(f"Ошибка: {e}", fg="red"), err=True)


@cli.command()
@click.argument("name", required=False)
@click.option("--exact", is_flag=True, help="Точное совпадение названия")
def search(name: Optional[str], exact: bool) -> None:
    """Поиск маршрутов по названию."""
    if not container.routes:
        click.echo("Нет сохраненных маршрутов.")
        return

    if not name:
        name = click.prompt("Введите название для поиска")

    found_routes = container.search_by_name(str(name), exact)

    if found_routes:
        click.echo(f"Найдено маршрутов: {len(found_routes)}\n")
        for idx, route in enumerate(found_routes, 1):
            click.echo(
                f"{idx}. {route.name} - {route.distance} км ({route.difficulty})"
            )
    else:
        click.echo(
            click.style(f"Маршруты по запросу '{name}' не найдены.", fg="yellow")
        )


@cli.command()
@click.confirmation_option(prompt="Вы уверены, что хотите очистить все маршруты?")
def clear() -> None:
    """Очистить все маршруты."""
    container.routes = []
    click.echo(click.style("✓ Все маршруты очищены", fg="green"))
    click.echo("  Используйте команду 'save' для сохранения изменений")


@cli.command()
@click.option("--count", is_flag=True, help="Показать только количество")
def stats(count: bool) -> None:
    """Показать статистику по маршрутам."""
    if not container.routes:
        click.echo("Нет сохраненных маршрутов.")
        return

    if count:
        click.echo(f"Всего маршрутов: {len(container.routes)}")
        return

    total_distance = container.get_total_distance()
    avg_distance = total_distance / len(container.routes)

    difficulties = container.get_difficulty_stats()

    click.echo("Статистика маршрутов:\n")
    click.echo(f"Всего маршрутов: {len(container.routes)}")
    click.echo(f"Общее расстояние: {total_distance:.1f} км")
    click.echo(f"Среднее расстояние: {avg_distance:.1f} км")
    click.echo("\nРаспределение по сложности:")
    for diff, cnt in difficulties.items():
        percentage = (cnt / len(container.routes)) * 100
        click.echo(f"  {diff}: {cnt} ({percentage:.1f}%)")


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Показать информацию о текущем состоянии."""
    data_file = ctx.obj["data_file"]
    click.echo("Информация о системе:\n")
    click.echo(f"Файл данных: {data_file}")
    click.echo(f"Всего маршрутов: {len(container.routes)}")

    if os.path.exists(str(data_file)):
        file_size = os.path.getsize(str(data_file))
        click.echo(f"Размер файла: {file_size} байт")
    else:
        click.echo("Файл данных не существует")

    if container.routes:
        click.echo("\nПоследние добавленные маршруты:")
        for route in container.routes[-3:]:
            click.echo(f"  • {route.name} ({route.distance} км, {route.difficulty})")


if __name__ == "__main__":
    cli()
