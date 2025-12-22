from coach.time_parser import parse_time_query, resolve_time_query

tests = [
    "résume ma semaine",
    "résumé de la semaine dernière",
    "il y a 2 semaines",
    "ce mois",
    "mois dernier",
    "du 10 au 24 décembre",
]

for t in tests:
    tq = parse_time_query(t)
    start, end = resolve_time_query(tq)
    print(t, "→", start, end)
