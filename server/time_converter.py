def convert_time(text):
    try:
        t = text.lower().replace(",", ".")

        if " у " not in t:
            return None

        left, unit2 = t.split(" у ")
        value, unit1 = left.split()

        value = float(value)

        # Секунди ↔ хвилини
        if unit1 == "с" and unit2 == "хв":
            return str(value / 60)

        if unit1 == "хв" and unit2 == "с":
            return str(value * 60)

        # Хвилини ↔ години
        if unit1 == "хв" and unit2 == "год":
            return str(value / 60)

        if unit1 == "год" and unit2 == "хв":
            return str(value * 60)

        # Години ↔ дні
        if unit1 == "год" and unit2 == "дні":
            return str(value / 24)

        if unit1 == "дні" and unit2 == "год":
            return str(value * 24)

        # Дні ↔ тижні
        if unit1 == "дні" and unit2 == "тиж":
            return str(value / 7)

        if unit1 == "тиж" and unit2 == "дні":
            return str(value * 7)

        return None

    except:
        return None
