import pandas as pd
import csv
from datetime import datetime
from data_entry import get_date, get_amount, get_category, get_description
import matplotlib.pyplot as plt

class CSV:
    CSV_FILE = "finance_data.csv"
    COLUMNS = ["Date", "Amount", "Category", "Description"]
    FORMAT = "%d-%m-%Y"

    @classmethod
    def initialize_csv(cls):
        try:
            pd.read_csv(cls.CSV_FILE)
        except FileNotFoundError:
            df = pd.DataFrame(columns=cls.COLUMNS)
            df.to_csv(cls.CSV_FILE, index=False)

    @classmethod
    def add_entry(cls, Date, Amount, Category, Description):
        new_entry = {
            "Date": Date,
            "Amount": Amount,
            "Category": Category,
            "Description": Description
        }
        with open(cls.CSV_FILE, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=cls.COLUMNS)
            writer.writerow(new_entry)
        print("Enttry added successfully.")

    @classmethod
    def get_transactions(cls, start_date, end_date):
        df =pd.read_csv(cls.CSV_FILE)
        df["Date"] = pd.to_datetime(df["Date"], format=CSV.FORMAT)
        start_date = datetime.strptime(start_date, CSV.FORMAT)
        end_date = datetime.strptime(end_date, CSV.FORMAT)

        mask = (df["Date"] >= start_date) & (df["Date"] <= end_date)
        filtered_df = df.loc[mask]

        if filtered_df.empty:
            print("No transactions found in the given date range.")
        else:
            print(f"Transactions from {start_date.strftime(CSV.FORMAT)} to {end_date.strftime(CSV.FORMAT)} : ")
            print(filtered_df.to_string(index=False, formatters={"Date" : lambda x: x.strftime(CSV.FORMAT)}))
            total_income = filtered_df[filtered_df["Category"] == "Income"]["Amount"].sum()
            total_expense = filtered_df[filtered_df["Category"] == "Expense"]["Amount"].sum()
            print("\nSummary:")
            print(f"Total Income: ${total_income:.2f}")
            print(f"Total Expense: ${total_expense:.2f}")
            print(f"Net Savings: ${(total_income - total_expense):.2f}")

        return filtered_df
    

def add():
    CSV.initialize_csv()
    Date = get_date("Enter the date of the Transaction (DD-MM-YYYY) OR enter for today's date : ", allow_default=True)
    Amount = get_amount()
    Category = get_category()
    Description = get_description()
    CSV.add_entry(Date, Amount, Category, Description)

def plot_transactions(df):
    df.set_index("Date", inplace=True)

    income_df = (
        df[df["Category"] == "Income"]["Amount"]
            .resample("D")
            .sum()
        )

    expense_df = (
        df[df["Category"] == "Expense"]["Amount"]
            .resample("D")
            .sum()
        )
    Dates = pd.date_range(df.index.min(), df.index.max())

    income = income_df.reindex(Dates, fill_value=0)
    expense = expense_df.reindex(Dates, fill_value=0)

    plt.figure(figsize=(10,6))
    plt.plot(income.index, income, label="Income", color="g")
    plt.plot(expense.index, expense, label="Expense", color="r")
    plt.title("Income and Expense Over Time")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.show()


def main():
    while True:
        print("\n1. Add a new Transaction")
        print("2. View Transactions & Summary within a date range")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ")

        if choice == "1":
            add()

        elif choice == "2":
            start_date = get_date("Enter the start date (DD-MM-YYYY): ")
            end_date = get_date("Enter the end date (DD-MM-YYYY): ")
            df = CSV.get_transactions(start_date, end_date)
            if input("Do you want to see a plot of transactions? (y/n): ").lower() == "y":
                plot_transactions(df)
                

        elif choice == "3":
            print("EXITING...")
            break

        else:
            print("Invalid chice. Enter 1, 2 or 3.")

if __name__ == "__main__":
    main()