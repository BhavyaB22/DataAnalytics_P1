import pymysql
import pandas as pd
import matplotlib.pyplot as plt

# Connect to MySQL
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='digitalprescription_db'
)

# Disable ONLY_FULL_GROUP_BY for this session
cursor = conn.cursor()
cursor.execute("""
SET SESSION sql_mode =
(REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''))
""")
cursor.close()

def run_query(sql):
    return pd.read_sql_query(sql, conn)

# -----------------------------------------------
# Load all query results once at the start
# CLI will just print these - no repeated queries
# -----------------------------------------------

q1 = run_query('''
    SELECT d.drug_name, d.drug_category,
           COUNT(p.prescription_id) AS prescription_count
    FROM prescriptions p
    JOIN drugs d ON p.drug_id = d.drug_id
    GROUP BY d.drug_id, d.drug_name, d.drug_category
    ORDER BY prescription_count DESC
    LIMIT 10
''')

q2 = run_query('''
    SELECT pt.gender,
           COUNT(pr.prescription_id) AS total_prescriptions
    FROM prescriptions pr
    JOIN admissions a ON pr.admission_id = a.admission_id
    JOIN patients pt  ON a.patient_id    = pt.patient_id
    GROUP BY pt.gender
''')

q3 = run_query('''
    SELECT
        CASE
            WHEN pt.age < 18 THEN '0-18'
            WHEN pt.age < 35 THEN '19-35'
            WHEN pt.age < 50 THEN '36-50'
            WHEN pt.age < 65 THEN '51-65'
            ELSE '65+'
        END AS age_group,
        COUNT(pr.prescription_id) AS total_prescriptions,
        ROUND(AVG(pr.duration_days), 1) AS avg_duration_days
    FROM prescriptions pr
    JOIN admissions a ON pr.admission_id = a.admission_id
    JOIN patients pt  ON a.patient_id    = pt.patient_id
    GROUP BY age_group
    ORDER BY MIN(pt.age)
''')

q4 = run_query('''
    SELECT dep.department_name,
           COUNT(pr.prescription_id) AS total_prescriptions,
           COUNT(DISTINCT a.patient_id) AS unique_patients
    FROM prescriptions pr
    JOIN admissions a    ON pr.admission_id  = a.admission_id
    JOIN departments dep ON a.department_id  = dep.department_id
    GROUP BY dep.department_id, dep.department_name
    ORDER BY total_prescriptions DESC
''')



q5 = run_query('''
    SELECT e.employee_name AS doctor_name,
           dep.department_name,
           COUNT(pr.prescription_id) AS total_prescriptions
    FROM prescriptions pr
    JOIN admissions a    ON pr.admission_id  = a.admission_id
    JOIN employees e     ON e.department_id  = a.department_id
                         AND e.role = 'Doctor'
    JOIN departments dep ON dep.department_id = a.department_id
    GROUP BY e.employee_id,
             e.employee_name,
             dep.department_name
    ORDER BY total_prescriptions DESC
    LIMIT 15
''')
avg = q5['total_prescriptions'].mean()
std = q5['total_prescriptions'].std()
q5['is_outlier'] = q5['total_prescriptions'] >= (avg + 1.5 * std)

q6 = run_query('''
    SELECT dis.disease_name,
           dis.disease_category,
           COUNT(a.admission_id) AS total_cases
    FROM admissions a
    JOIN diseases dis ON a.disease_id = dis.disease_id
    GROUP BY dis.disease_id,
             dis.disease_name,
             dis.disease_category
    ORDER BY total_cases DESC
    LIMIT 10
''')

q7 = run_query('''
    SELECT d.drug_category,
           COUNT(pr.prescription_id) AS times_prescribed
    FROM prescriptions pr
    JOIN drugs d ON pr.drug_id = d.drug_id
    GROUP BY d.drug_category
    ORDER BY times_prescribed DESC
''')

q8 = run_query('''
    SELECT admission_type,
           COUNT(*) AS total_admissions
    FROM admissions
    GROUP BY admission_type
    ORDER BY total_admissions DESC
''')

q9 = run_query('''
    SELECT d.drug_name, d.drug_category,
           di.current_stock, di.reorder_level,
           di.inventory_status
    FROM drug_inventory di
    JOIN drugs d ON di.drug_id = d.drug_id
    WHERE di.current_stock <= di.reorder_level
    ORDER BY di.current_stock ASC
    LIMIT 15
''')

q10 = run_query('''
    SELECT
        DATE_FORMAT(a.admission_date,'%Y-%m') AS month,
        COUNT(pr.prescription_id) AS total_prescriptions
    FROM prescriptions pr
    JOIN admissions a
         ON pr.admission_id = a.admission_id
    GROUP BY month
    ORDER BY month
''')

total_patients      = run_query('SELECT COUNT(*) AS c FROM patients').iloc[0]['c']
total_admissions    = run_query('SELECT COUNT(*) AS c FROM admissions').iloc[0]['c']
total_prescriptions = run_query('SELECT COUNT(*) AS c FROM prescriptions').iloc[0]['c']
total_drugs         = run_query('SELECT COUNT(*) AS c FROM drugs').iloc[0]['c']

print('Data loaded from MySQL.')

# -----------------------------------------------
# MENU
# -----------------------------------------------

menu = """
=========================================
  PRESCRIPTION RECORD - ANALYTICS MENU
=========================================
  1.  Quick Stats
  2.  Top 10 Prescribed Medicines
  3.  Gender-wise Distribution
  4.  Age Group vs Prescriptions
  5.  Department-wise Volume
  6.  Doctor Prescription Volume
  7.  Top 10 Diseases
  8.  Drug Category Breakdown
  9. Low Drug Inventory Alert
  10. Montly Prescription Trend  
  0.  Exit
========================================="""
while True:
    print(menu)
    choice = input("Enter your choice: ").strip()

    if choice == '0':
        print("Goodbye!")
        break

    elif choice == '1':
        print("\n--- Quick Stats ---")
        print("Total Patients      :", total_patients)
        print("Total Admissions    :", total_admissions)
        print("Total Prescriptions :", total_prescriptions)
        print("Total Drugs         :", total_drugs)

    elif choice == '2':
        plt.figure(figsize=(10,6))
        plt.barh(
            q1['drug_name'],
            q1['prescription_count']
        )
        plt.title('Top 10 Prescribed Medicines')
        plt.xlabel('Prescription Count')
        plt.tight_layout()
        plt.show()

    elif choice == '3':
        plt.figure(figsize=(8,8))
        plt.pie(
            q2['total_prescriptions'],
            labels=q2['gender'],
            autopct='%1.1f%%'
        )
        plt.title('Gender-wise Prescription Distribution')
        plt.show()

    elif choice == '4':


        plt.figure(figsize=(8,4.5), facecolor='white')

        colors = [
            '#A8DADC',   # light teal
            '#F4A261',   # soft orange
            '#8FD694',   # soft green
            '#7FB3D5',   # soft blue
            '#C39BD3'    # soft purple
        ]

        bars = plt.bar(
            q3['age_group'],
            q3['total_prescriptions'],
            color=colors,
            edgecolor='#D0D0D0',
            linewidth=0.8
        )

        for bar in bars:
            h = bar.get_height()

            plt.text(
                bar.get_x() + bar.get_width()/2,
                h + (h*0.01),
                f'{int(h):,}',
                ha='center',
                fontsize=9,
                color='#444444'
            )

        plt.title(
            'Age Group vs Prescriptions',
            fontsize=15,
            weight='bold',
            color='#1F2937'
        )

        plt.xlabel('')
        plt.ylabel('Prescription Count')

        plt.grid(
            axis='y',
            linestyle='--',
            alpha=0.2
        )

        plt.box(False)

        plt.tight_layout()
        plt.show()


    elif choice == '5':

        plt.figure(figsize=(10,5))

        plt.bar(
            q4['department_name'],
            q4['total_prescriptions']
        )

        plt.title('Department-wise Prescription Volume')

        plt.xticks(rotation=30)

        plt.tight_layout()
        plt.show()

    elif choice == '6':

        plt.figure(figsize=(12,6))

        top_doctors = q5.head(10).sort_values(
            'total_prescriptions',
            ascending=True
        )

        plt.barh(
            top_doctors['doctor_name'],
            top_doctors['total_prescriptions']
        )

        plt.title('Doctor-wise Prescription Volume')
        plt.xlabel('Total Prescriptions')

        plt.tight_layout()
        plt.show()


    elif choice == '7':

        plt.figure(figsize=(12,6))

        plt.barh(
            q6['disease_name'],
            q6['total_cases']
        )

        plt.title('Top Diseases')
        plt.xlabel('Total Cases')

        plt.tight_layout()
        plt.show()

    elif choice == '8':

        plt.figure(figsize=(8,8))

        plt.pie(
            q7['times_prescribed'],
            labels=q7['drug_category'],
            autopct='%1.1f%%'
        )

        plt.title('Drug Category Distribution')
        plt.show()

    elif choice == '9':

        plt.figure(figsize=(12,6))

        plt.barh(
            q9['drug_name'],
            q9['current_stock']
        )

        plt.title('Low Inventory Drugs')
        plt.xlabel('Current Stock')

        plt.tight_layout()
        plt.show()
    elif choice == '10':

        plt.style.use('seaborn-v0_8-whitegrid')

        q10['moving_avg'] = (
            q10['total_prescriptions']
            .rolling(window=3)
            .mean()
        )

        plt.figure(figsize=(10, 4.5), facecolor='white')

        # Monthly prescriptions
        plt.plot(
            q10['month'],
            q10['total_prescriptions'],
            color='#4F81BD',
            linewidth=2,
            alpha=0.8,
            label='Monthly Prescriptions'
        )

        # Moving average
        plt.plot(
            q10['month'],
            q10['moving_avg'],
            color='#E74C3C',
            linewidth=2.5,
            label='3-Month Moving Avg'
        )

        plt.title(
            'Monthly Prescription Trend',
            fontsize=15,
            fontweight='bold',
            color='#1F2937'
        )

        plt.xlabel('Month', fontsize=10)
        plt.ylabel('Prescription Count', fontsize=10)

        # Show every 6th month
        plt.xticks(
            range(0, len(q10), 6),
            q10['month'][::6],
            rotation=30
        )

        plt.legend(
            frameon=False,
            loc='upper right'
        )

        plt.grid(
            axis='y',
            linestyle='--',
            alpha=0.25
        )

        ax = plt.gca()

        # Remove unnecessary borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        plt.show()

        input("\nPress Enter to return to menu...")

    else:
        print("Invalid choice. Please enter a number from 0 to 10.")

conn.close()