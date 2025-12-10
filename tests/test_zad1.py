#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from task_package.zad1 import Route, RouteContainer


class TestRoute:
    """Тесты для класса Route."""

    def test_route_creation(self):
        """Тест создания объекта Route."""
        route = Route(name="Горный поход", distance=15.5, difficulty="средний")
        assert route.name == "Горный поход"
        assert route.distance == 15.5
        assert route.difficulty == "средний"

    def test_route_immutability(self):
        """Тест на неизменяемость Route."""
        route = Route(name="Тест", distance=10.0, difficulty="легкий")

        # Проверяем, что объект хешируемый (необходимо для frozen dataclass)
        assert hash(route) is not None

        # Проверяем, что поля доступны только для чтения
        with pytest.raises(AttributeError):
            route.name = "Новое имя"

    def test_route_equality(self):
        """Тест на сравнение объектов Route."""
        route1 = Route(name="Поход", distance=10.0, difficulty="легкий")
        route2 = Route(name="Поход", distance=10.0, difficulty="легкий")
        route3 = Route(name="Другой поход", distance=20.0, difficulty="сложный")

        assert route1 == route2
        assert route1 != route3


class TestRouteContainer:
    """Тесты для класса RouteContainer."""

    @pytest.fixture
    def container(self):
        """Фикстура для создания пустого контейнера."""
        return RouteContainer()

    @pytest.fixture
    def populated_container(self):
        """Фикстура для создания контейнера с данными."""
        container = RouteContainer()
        container.add_route("Горный поход", 15.5, "средний")
        container.add_route("Лесная прогулка", 8.0, "легкий")
        container.add_route("Водный маршрут", 25.0, "сложный")
        return container

    def test_add_route(self, container):
        """Тест добавления маршрута."""
        assert container.get_route_count() == 0

        container.add_route("Тестовый маршрут", 10.0, "средний")
        assert container.get_route_count() == 1

        # Проверяем, что маршрут добавлен корректно
        route = container.routes[0]
        assert route.name == "Тестовый маршрут"
        assert route.distance == 10.0
        assert route.difficulty == "средний"

    def test_add_route_invalid_difficulty(self, container):
        """Тест добавления маршрута с некорректной сложностью."""
        with pytest.raises(
            ValueError, match="Сложность должна быть 'легкий', 'средний' или 'сложный'"
        ):
            container.add_route("Тест", 10.0, "неверная")

    def test_display_all_empty(self, container):
        """Тест отображения пустого контейнера."""
        result = container.display_all()
        assert result == "Нет сохраненных маршрутов."

    def test_display_all_populated(self, populated_container):
        """Тест отображения контейнера с данными."""
        result = populated_container.display_all()

        # Проверяем, что вывод содержит ожидаемые данные
        assert "Горный поход" in result
        assert "Лесная прогулка" in result
        assert "Водный маршрут" in result
        assert "15.5" in result
        assert "8.0" in result
        assert "25.0" in result

    def test_select_by_distance(self, populated_container):
        """Тест выбора маршрутов по расстоянию."""
        # Маршруты длиннее 10 км
        result = populated_container.select_by_distance(10.0)
        assert len(result) == 2
        assert all(route.distance > 10.0 for route in result)

        # Маршруты длиннее 20 км
        result = populated_container.select_by_distance(20.0)
        assert len(result) == 1
        assert result[0].name == "Водный маршрут"

        # Маршруты длиннее 100 км
        result = populated_container.select_by_distance(100.0)
        assert len(result) == 0

    def test_get_route_count(self, populated_container):
        """Тест получения количества маршрутов."""
        assert populated_container.get_route_count() == 3

    def test_clear_routes(self, populated_container):
        """Тест очистки маршрутов."""
        assert populated_container.get_route_count() == 3
        populated_container.clear_routes()
        assert populated_container.get_route_count() == 0
        assert populated_container._current_file is None

    def test_get_total_distance(self, populated_container):
        """Тест расчета общего расстояния."""
        total = populated_container.get_total_distance()
        expected = 15.5 + 8.0 + 25.0
        assert total == expected

    def test_save_and_load_xml(self):
        """Тест сохранения и загрузки XML."""
        container = RouteContainer()
        container.add_route("Тест 1", 10.0, "легкий")
        container.add_route("Тест 2", 20.0, "средний")

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            temp_file = f.name

        try:
            # Сохраняем
            saved_file = container.save_to_xml(temp_file)
            assert saved_file == temp_file

            # Создаем новый контейнер и загружаем
            new_container = RouteContainer()
            new_container.load_from_xml(temp_file)

            # Проверяем, что данные загружены корректно
            assert new_container.get_route_count() == 2

            # Проверяем, что маршруты загружены в правильном порядке
            assert new_container.routes[0].name == "Тест 1"
            assert new_container.routes[0].distance == 10.0
            assert new_container.routes[0].difficulty == "легкий"

            assert new_container.routes[1].name == "Тест 2"
            assert new_container.routes[1].distance == 20.0
            assert new_container.routes[1].difficulty == "средний"

            # Проверяем, что текущий файл установлен
            assert new_container._current_file == temp_file

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_xml_empty_container(self):
        """Тест сохранения пустого контейнера."""
        container = RouteContainer()
        with pytest.raises(ValueError, match="Нет маршрутов для сохранения"):
            container.save_to_xml("test.xml")

    def test_load_xml_nonexistent_file(self):
        """Тест загрузки несуществующего файла."""
        container = RouteContainer()
        with pytest.raises(FileNotFoundError):
            container.load_from_xml("nonexistent.xml")

    def test_save_to_xml_default_filename(self):
        """Тест сохранения с именем файла по умолчанию."""
        container = RouteContainer()
        container.add_route("Тест", 10.0, "легкий")

        # Сохраняем без указания имени файла
        saved_file = container.save_to_xml()
        assert saved_file == "routes.xml"

        # Очищаем
        if os.path.exists("routes.xml"):
            os.unlink("routes.xml")

    def test_save_to_xml_with_current_file(self):
        """Тест сохранения с использованием текущего файла."""
        container = RouteContainer()
        container.add_route("Тест", 10.0, "легкий")

        # Сначала сохраняем в один файл
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            temp_file1 = f.name

        # Сначала сохраняем в temp_file1
        saved_file = container.save_to_xml(temp_file1)
        assert saved_file == temp_file1
        assert container._current_file == temp_file1

        # Добавляем еще маршрут и сохраняем без указания имени файла
        container.add_route("Тест 2", 20.0, "средний")
        saved_file = container.save_to_xml()

        # Должен сохраниться в текущий файл
        assert saved_file == temp_file1

        # Проверяем, что файл существует
        assert os.path.exists(temp_file1)

        # Очищаем
        if os.path.exists(temp_file1):
            os.unlink(temp_file1)


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_cycle(self):
        """Полный цикл: создание, добавление, сохранение, загрузка."""
        # Создаем контейнер
        container = RouteContainer()

        # Добавляем маршруты
        container.add_route("Интеграционный тест 1", 15.0, "средний")
        container.add_route("Интеграционный тест 2", 8.5, "легкий")

        assert container.get_route_count() == 2
        assert container.get_total_distance() == 23.5

        # Сохраняем
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            temp_file = f.name

        try:
            saved_file = container.save_to_xml(temp_file)
            assert saved_file == temp_file

            # Проверяем, что файл создан
            assert os.path.exists(temp_file)

            # Проверяем содержимое файла
            tree = ET.parse(temp_file)
            root = tree.getroot()
            assert root.tag == "routes"
            assert len(root.findall("route")) == 2

            # Загружаем в новый контейнер
            new_container = RouteContainer()
            new_container.load_from_xml(temp_file)

            # Проверяем загруженные данные
            assert new_container.get_route_count() == 2
            assert new_container.get_total_distance() == 23.5

            # Проверяем выборку
            selected = new_container.select_by_distance(10.0)
            assert len(selected) == 1
            assert selected[0].name == "Интеграционный тест 1"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_display_format(self):
        """Тест формата отображения."""
        container = RouteContainer()
        container.add_route("А", 10.0, "легкий")
        container.add_route("Б", 20.0, "средний")

        display = container.display_all()

        # Проверяем наличие заголовков таблицы
        assert "№" in display
        assert "Название маршрута" in display
        assert "Расстояние (км)" in display
        assert "Сложность" in display

        # Проверяем наличие данных
        assert "А" in display
        assert "10.0" in display
        assert "легкий" in display
        assert "Б" in display
        assert "20.0" in display
        assert "средний" in display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
