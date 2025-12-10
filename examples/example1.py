#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from typing import List


@dataclass(frozen=True)
class Worker:
    name: str
    post: str
    year: int


@dataclass
class Staff:
    workers: List[Worker] = field(default_factory=list)

    def add(self, name: str, post: str, year: int) -> None:
        self.workers.append(Worker(name=name, post=post, year=year))

    def __str__(self) -> str:
        # Сортируем по имени перед выводом
        sorted_workers = sorted(self.workers, key=lambda worker: worker.name)

        table = []
        line = "+{}+{}+{}+{}+".format("-" * 4, "-" * 30, "-" * 20, "-" * 8)
        table.append(line)
        table.append(
            "| {:^4} | {:^30} | {:^20} | {:^8} |".format(
                "№", "Ф.И.О.", "Должность", "Год"
            )
        )
        table.append(line)

        for idx, worker in enumerate(sorted_workers, 1):
            table.append(
                "| {:^4} | {:^30} | {:^20} | {:^8} |".format(
                    idx, worker.name, worker.post, worker.year
                )
            )
        table.append(line)
        return "\n".join(table)

    def select(self, period: int) -> List[Worker]:
        today = date.today()
        result: List[Worker] = []
        for worker in self.workers:
            if today.year - worker.year >= period:
                result.append(worker)
        return result

    def load(self, filename: str) -> None:
        self.workers = []  # Очищаем текущий список

        with open(filename, "r", encoding="utf-8") as fin:
            xml = fin.read()

        parser = ET.XMLParser(encoding="utf-8")
        root = ET.fromstring(xml, parser=parser)

        for worker_element in root:
            name, post, year = None, None, None

            for element in worker_element:
                if element.tag == "name":
                    name = element.text
                elif element.tag == "post":
                    post = element.text
                elif element.tag == "year":
                    year = int(element.text)

            if name is not None and post is not None and year is not None:
                self.workers.append(Worker(name=name, post=post, year=year))

    def save(self, filename: str) -> None:
        root = ET.Element("workers")
        for worker in self.workers:
            worker_element = ET.Element("worker")

            name_element = ET.SubElement(worker_element, "name")
            name_element.text = worker.name

            post_element = ET.SubElement(worker_element, "post")
            post_element.text = worker.post

            year_element = ET.SubElement(worker_element, "year")
            year_element.text = str(worker.year)

            root.append(worker_element)

        tree = ET.ElementTree(root)
        with open(filename, "wb") as fout:
            tree.write(fout, encoding="utf-8", xml_declaration=True)


# =========================
# CLI-БЛОК
# =========================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Система учёта сотрудников (dataclass + XML + аттрибуты)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_parser = subparsers.add_parser("add", help="Добавить сотрудника")
    add_parser.add_argument("--name", required=True, help="Фамилия и инициалы")
    add_parser.add_argument("--post", required=True, help="Должность")
    add_parser.add_argument("--year", required=True, type=int, help="Год поступления")

    # list
    subparsers.add_parser("list", help="Показать всех сотрудников")

    # select
    select_parser = subparsers.add_parser("select", help="Выбрать по стажу")
    select_parser.add_argument("--period", required=True, type=int, help="Стаж (годы)")

    # load
    load_parser = subparsers.add_parser("load", help="Загрузить из XML")
    load_parser.add_argument("filename", help="Имя XML файла")

    # save
    save_parser = subparsers.add_parser("save", help="Сохранить в XML")
    save_parser.add_argument("filename", help="Имя XML файла")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    staff = Staff()

    # Команды
    if args.command == "add":
        staff.add(args.name, args.post, args.year)
        print("Сотрудник добавлен.")

    elif args.command == "list":
        print(staff)

    elif args.command == "select":
        selected = staff.select(args.period)
        if selected:
            for idx, worker in enumerate(selected, 1):
                print(f"{idx:>4}: {worker.name}")
        else:
            print("Работники с заданным стажем не найдены.")

    elif args.command == "load":
        staff.load(args.filename)
        print(f"Данные загружены из {args.filename}")

    elif args.command == "save":
        staff.save(args.filename)
        print(f"Данные сохранены в {args.filename}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
