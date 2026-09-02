import math
import random

def calculate(expression):
    expr = expression.strip()

    expr = expr.replace("×", "*")
    expr = expr.replace("÷", "/")
    expr = expr.replace(":", "/")
    expr = expr.replace("^", "**")
    expr = expr.replace("√", "sqrt")

    # Відсотки
    try:
        if "%" in expr and "від" in expr:
            left, right = expr.replace("%", "").split("від")
            percent = float(left.strip())
            number = float(right.strip())
            return str(number * percent / 100)
    except:
        pass

    # Температура
    try:
        t = expr.lower().replace("°", "")

        if " у " in t:
            parts = t.split(" у ")

            left = parts[0].split()

            if len(left) == 2:
                value = float(left[0])
                unit1 = left[1]
                unit2 = parts[1]

                if unit1 == "c" and unit2 == "f":
                    return str(value * 9 / 5 + 32)

                if unit1 == "f" and unit2 == "c":
                    return str((value - 32) * 5 / 9)

                if unit1 == "c" and unit2 == "k":
                    return str(value + 273.15)

                if unit1 == "k" and unit2 == "c":
                    return str(value - 273.15)

                if unit1 == "f" and unit2 == "k":
                    return str((value - 32) * 5 / 9 + 273.15)

                if unit1 == "k" and unit2 == "f":
                    return str((value - 273.15) * 9 / 5 + 32)

                # Довжина
                if unit1 == "км" and unit2 == "м":
                    return str(value * 1000)

                if unit1 == "м" and unit2 == "км":
                    return str(value / 1000)

                if unit1 == "м" and unit2 == "см":
                    return str(value * 100)

                if unit1 == "см" and unit2 == "м":
                    return str(value / 100)

                if unit1 == "см" and unit2 == "мм":
                    return str(value * 10)

                if unit1 == "мм" and unit2 == "см":
                    return str(value / 10)
    except:
        pass

    allowed = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log10,
        "ln": math.log,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "pow": pow,
        "factorial": math.factorial,
        "randint": random.randint,
        "min": min,
        "max": max,
    }

    try:
        result = eval(expr, {"__builtins__": {}}, allowed)
        return str(result)
    except:
        return None
