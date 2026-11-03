# PyFlow

Biblioteka do definiowania przepływów danych: zadania, zależności,
walidacja DAG i deterministyczny plan wykonania.

## Instalacja

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/Mac: source .venv/bin/activate
pip install -e ".[dev]"
```

## Testy

```bash
python -m pytest
```

## Przykład

```python
from pyflow import Task, Workflow, execution_layers, topological_order

wf = Workflow()
wf.add_task(Task("extract", lambda inputs, params: [1, 2, 3]))
wf.add_task(Task("clean_a", lambda i, p: None, frozenset({"extract"})))
wf.add_task(Task("clean_b", lambda i, p: None, frozenset({"extract"})))
wf.add_task(Task("report", lambda i, p: None, frozenset({"clean_a", "clean_b"})))

wf.validate()
print(topological_order(wf))  # ['extract', 'clean_a', 'clean_b', 'report']
print(execution_layers(wf))   # [['extract'], ['clean_a', 'clean_b'], ['report']]
```

## Algorytm i złożoność

Użyto algorytmu Kahna. Dla każdego zadania liczony jest stopień wejściowy
(liczba zależności); zadania z zerem zależności tworzą pierwszą warstwę,
po jej "wykonaniu" zmniejszamy liczniki zależnych zadań i tak powstają
kolejne warstwy. Jeśli nie wszystkie zadania zostały przetworzone, w grafie
jest cykl i zgłaszany jest `WorkflowValidationError`.

Złożoność: O(V + E) dla przetwarzania grafu oraz O(V log V) dla sortowania
nazw w warstwach (V - liczba zadań, E - liczba zależności).
Sortowanie alfabetyczne w warstwie zapewnia deterministyczny wynik.