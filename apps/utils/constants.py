# utils/constants.py

# Kunlar (Du, Se, ...)
DAY_NAMES = [
    "Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"
]

# Oylar (Yan, Fev, ...)
MONTH_NAMES = [
    "Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek"
]

UZ_MONTHS = {
    i + 1: month for i, month in enumerate(MONTH_NAMES)
}
