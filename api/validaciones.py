def validar_ventana(inicio: int | None, fin: int | None) -> None:
    """Una ventana horaria (minuto del día) es completa o no existe: inicio y
    fin juntos, con el fin estrictamente después del inicio."""
    if (inicio is None) != (fin is None):
        raise ValueError("La ventana horaria necesita hora de inicio y de fin.")
    if inicio is not None and fin is not None and fin <= inicio:
        raise ValueError("La ventana horaria debe terminar después de empezar.")
