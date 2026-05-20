CPU_COST_PER_HOUR = 0.05

HOURS_PER_MONTH = 730


def estimate_cpu_savings(reduced_cpu):

    monthly_savings = (
        reduced_cpu
        * CPU_COST_PER_HOUR
        * HOURS_PER_MONTH
    )

    return round(monthly_savings, 2)