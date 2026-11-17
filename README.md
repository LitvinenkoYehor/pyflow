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

## Silnik wykonawczy (Laboratorium 2)

```python
from pyflow import run, format_report

result = run(workflow)
result.outputs       # nazwa zadania -> zwrócona wartość
result.task_states   # nazwa zadania -> TaskState (status, czasy, błąd)
result.succeeded     # True, gdy wszystkie zadania zakończyły się sukcesem
print(format_report(result))  # raport tekstowy z czasami
```

### Kontrakt funkcji zadania

Każda funkcja ma postać `function(inputs, params)`. `inputs` to mapowanie
(tylko do odczytu) `nazwa bezpośredniej zależności -> jej wynik`; `params`
to konfiguracja zadania. Funkcje są synchroniczne.

### Statusy

`PENDING` (jeszcze nie uruchomione), `RUNNING`, `SUCCEEDED`, `FAILED`
(funkcja rzuciła wyjątek), `SKIPPED` (zadanie zależy od zadania, które nie
zakończyło się sukcesem).

### Polityka błędów

Po awarii zadanie dostaje `FAILED`, a jego następniki (także pośrednie)
`SKIPPED` – ich funkcje nie są wywoływane. Zadania niezależne od
uszkodzonej gałęzi są DOKOŃCZONE (nie ma fail-fast). Błąd jest zapisany w
`result.task_states[nazwa].error` jako `TaskExecutionError` z nazwą zadania
i oryginalnym wyjątkiem w `__cause__`. `run(wf, raise_on_failure=True)`
dodatkowo rzuca ten wyjątek po zakończeniu przebiegu.

### Przykład end-to-end

```bash
python examples/csv_report.py
```

Czyta `examples/data/sales.csv`, odrzuca niepoprawne rekordy, agreguje
przychód po regionach i zapisuje `examples/report.json`.