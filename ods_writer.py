import pandas as pd
import site_parser
import staff_parser


def make_numbered_df(data, column_name):
    df = pd.DataFrame(data, columns=[column_name])
    df.insert(0, "№", range(1, len(df) + 1))
    return df


def create_ods(filename="omgtu.ods", target_letter="Б"):
    departments = site_parser.get_departments()
    faculties = site_parser.get_faculties()
    staff_df = staff_parser.get_staff_by_letter(target_letter)

    departments_df = make_numbered_df(departments, "Кафедра")
    faculties_df = make_numbered_df(faculties, "Факультет")

    with pd.ExcelWriter(filename, engine="odf") as writer:
        departments_df.to_excel(writer, sheet_name="1. Кафедры", index=False)
        faculties_df.to_excel(writer, sheet_name="2. Факультеты", index=False)
        staff_df.to_excel(writer, sheet_name="3. Сотрудники", index=False)

    print(f"Файл {filename} создан")
