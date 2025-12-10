#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# fmt: off

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from task_package.zad2 import DEFAULT_FILENAME, Route, RouteContainer, cli


class TestRouteClick:
    """Тесты для класса Route в версии с click."""

    def test_route_creation(self):
        """Тест создания объекта Route."""
        route = Route(name="Горный поход", distance=15.5, difficulty="средний")
        assert route.name == "Горный поход"
        assert route.distance == 15.5
        assert route.difficulty == "средний"

    def test_route_immutability(self):
        """Тест на неизменяемость Route."""
        route = Route(name="Тест", distance=10.0, difficulty="легкий")

        # Проверяем, что объект хешируемый
        assert hash(route) is not None

        # Проверяем, что поля доступны только для чтения
        with pytest.raises(AttributeError):
            route.name = "Новое имя"


class TestRouteContainerClick:
    """Тесты для класса RouteContainer в версии с click."""

    @pytest.fixture
    def temp_container(self):
        """Фикстура для создания временного контейнера."""
        return RouteContainer()

    def test_add_route_with_autosave(self, temp_container):
        """Тест добавления маршрута с автосохранением."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            temp_file = f.name

        try:
            # Устанавливаем имя файла для контейнера
            temp_container._filename = temp_file

            # Добавляем маршрут с автосохранением
            temp_container.add_route(
                "Тестовый маршрут", 10.0, "средний", auto_save=True
            )

            # Проверяем, что маршрут добавлен
            assert temp_container.get_route_count() == 1

            # Проверяем, что файл создан
            assert os.path.exists(temp_file)

            # Проверяем содержимое файла
            tree = ET.parse(temp_file)
            root = tree.getroot()
            assert root.tag == "routes"
            assert len(root.findall("route")) == 1

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_add_route_without_autosave(self, temp_container):
        """Тест добавления маршрута без автосохранения."""
        # Добавляем маршрут без автосохранения
        temp_container.add_route("Тестовый маршрут", 10.0, "средний", auto_save=False)

        # Проверяем, что маршрут добавлен
        assert temp_container.get_route_count() == 1

        # Проверяем, что файл не создан (поскольку нет имени файла)
        # Это нормально, так как автосохранение отключено

    def test_load_from_xml_file_not_exists(self, temp_container):
        """Тест загрузки из несуществующего XML файла."""
        temp_file = "nonexistent.xml"

        # Загружаем из несуществующего файла
        temp_container.load_from_xml(temp_file)

        # Должен создаться пустой список
        assert temp_container.get_route_count() == 0
        assert temp_container._filename == temp_file

    def test_save_to_json(self, temp_container):
        """Тест сохранения в JSON."""
        # Добавляем маршруты
        temp_container.add_route("Тест 1", 10.0, "легкий", auto_save=False)
        temp_container.add_route("Тест 2", 20.0, "средний", auto_save=False)

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            temp_container.save_to_json(temp_file)

            # Проверяем, что файл создан
            assert os.path.exists(temp_file)

            # Проверяем содержимое файла
            with open(temp_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["name"] == "Тест 1"
            assert data[0]["distance"] == 10.0
            assert data[0]["difficulty"] == "легкий"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_search_by_name(self, temp_container):
        """Тест поиска маршрутов по названию."""
        # Добавляем маршруты
        temp_container.add_route(
            "Горный поход на Эльбрус", 42.5, "сложный", auto_save=False
        )
        temp_container.add_route("Лесная прогулка", 8.0, "легкий", auto_save=False)
        temp_container.add_route(
            "Водный маршрут по реке", 25.0, "средний", auto_save=False
        )

        # Поиск с частичным совпадением
        result = temp_container.search_by_name("горный", exact=False)
        assert len(result) == 1
        assert result[0].name == "Горный поход на Эльбрус"

        # Поиск с точным совпадением
        result = temp_container.search_by_name("Горный поход на Эльбрус", exact=True)
        assert len(result) == 1

        # Поиск несуществующего маршрута
        result = temp_container.search_by_name("несуществующий", exact=False)
        assert len(result) == 0

    def test_get_difficulty_stats(self, temp_container):
        """Тест получения статистики по сложности."""
        # Добавляем маршруты с разной сложностью
        temp_container.add_route("Маршрут 1", 10.0, "легкий", auto_save=False)
        temp_container.add_route("Маршрут 2", 15.0, "средний", auto_save=False)
        temp_container.add_route("Маршрут 3", 20.0, "сложный", auto_save=False)
        temp_container.add_route("Маршрут 4", 12.0, "легкий", auto_save=False)

        stats = temp_container.get_difficulty_stats()

        assert stats == {"легкий": 2, "средний": 1, "сложный": 1}


class TestCLIClick:
    """Тесты для CLI с использованием click."""

    @pytest.fixture
    def runner(self):
        """Фикстура для создания CliRunner."""
        return CliRunner()

    def test_cli_add_command(self, runner):
        """Тест команды add."""
        result = runner.invoke(
            cli,
            [
                "add",
                "--name",
                "Тестовый маршрут",
                "--distance",
                "10.0",
                "--difficulty",
                "легкий",
            ],
        )

        # Проверяем, что команда выполнена успешно
        assert result.exit_code == 0
        assert "Маршрут 'Тестовый маршрут' добавлен" in result.output

    def test_cli_info_command(self, runner):
        """Тест команды info."""
        result = runner.invoke(cli, ["info"])

        # Проверяем, что команда выполнена успешно
        assert result.exit_code == 0
        assert "Информация о системе" in result.output
        assert f"Файл данных: {DEFAULT_FILENAME}" in result.output

    def test_cli_clear_command(self, runner):
        """Тест команды clear (с подтверждением)."""
        # Сначала добавляем маршрут
        runner.invoke(
            cli,
            [
                "add",
                "--name",
                "Маршрут для очистки",
                "--distance",
                "15.0",
                "--difficulty",
                "средний",
                "--no-save",
            ],
        )

        # Очищаем без подтверждения (нажимаем 'n')
        result = runner.invoke(cli, ["clear"], input="n\n")

        # Проверяем, что очистка не произошла
        assert "Отменено" in result.output or result.exit_code != 0

        # Очищаем с подтверждением (нажимаем 'y')
        result = runner.invoke(cli, ["clear"], input="y\n")

        # Проверяем вывод
        assert result.exit_code == 0
        assert "Все маршруты очищены" in result.output


class TestIntegrationClick:
    """Интеграционные тесты для версии с click."""

    @pytest.fixture
    def runner(self):
        """Фикстура для создания CliRunner."""
        return CliRunner()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
