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
    SELECT DATE(a.admission_date) AS month,
           COUNT(pr.prescription_id) AS prescriptions
    FROM prescriptions pr
    JOIN admissions a ON pr.admission_id = a.admission_id
    WHERE a.admission_date IS NOT NULL
    GROUP BY DATE(a.admission_date)
    ORDER BY month
''')

q6 = run_query('''
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
avg = q6['total_prescriptions'].mean()
std = q6['total_prescriptions'].std()
q6['is_outlier'] = q6['total_prescriptions'] >= (avg + 1.5 * std)

q7 = run_query('''
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

q8 = run_query('''
    SELECT d.drug_category,
           COUNT(pr.prescription_id) AS times_prescribed
    FROM prescriptions pr
    JOIN drugs d ON pr.drug_id = d.drug_id
    GROUP BY d.drug_category
    ORDER BY times_prescribed DESC
''')

q9 = run_query('''
    SELECT admission_type,
           COUNT(*) AS total_admissions
    FROM admissions
    GROUP BY admission_type
    ORDER BY total_admissions DESC
''')

q10 = run_query('''
    SELECT d.drug_name, d.drug_category,
           di.current_stock, di.reorder_level,
           di.inventory_status
    FROM drug_inventory di
    JOIN drugs d ON di.drug_id = d.drug_id
    WHERE di.current_stock <= di.reorder_level
    ORDER BY di.current_stock ASC
    LIMIT 15
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
  6.  Monthly Prescription Trend
  7.  Doctor Prescription Volume
  8.  Top 10 Diseases
  9.  Drug Category Breakdown
  10. Admission Type Analysis
  11. Low Drug Inventory Alert
  0.  Exit
========================================="""
while True:
    print(menu)
    choice = input('Enter your choice: ').strip()

    if choice == '0':
        print('Goodbye!')
        break

    elif choice == '1':
        print('\n--- Quick Stats ---')
        print('Total Patients      :', total_patients)
        print('Total Admissions    :', total_admissions)
        print('Total Prescriptions :', total_prescriptions)
        print('Total Drugs         :', total_drugs)
        print('Low Stock Drugs     :', len(q10))

    elif choice == '2':
        plt.figure(figsize=(10,6))
        plt.barh(q1['drug_name'], q1['prescription_count'])
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
        plt.figure(figsize=(10,5))
        plt.bar(
            q3['age_group'],
            q3['total_prescriptions']
        )
        plt.title('Age Group vs Prescriptions')
        plt.xlabel('Age Group')
        plt.ylabel('Prescription Count')
        plt.tight_layout()
        plt.show()

    elif choice == '5':
        plt.figure(figsize=(10,5))
        plt.bar(
            q4['department_name'],
            q4['total_prescriptions']
        )
        plt.title('Department-wise Prescription Volume')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif choice == '6':
        plt.figure(figsize=(12,5))
        plt.plot(
            q5['month'],
            q5['prescriptions'],
            marker='o'
        )
        plt.title('Monthly Prescription Trend')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    elif choice == '7':
        plt.figure(figsize=(12,6))
        plt.barh(
            q6['doctor_name'],
            q6['total_prescriptions']
        )
        plt.title('Doctor Prescription Volume')
        plt.tight_layout()
        plt.show()

    elif choice == '8':
        plt.figure(figsize=(12,6))
        plt.barh(
            q7['disease_name'],
            q7['total_cases']
        )
        plt.title('Top 10 Diseases')
        plt.tight_layout()
        plt.show()

    elif choice == '9':
        plt.figure(figsize=(8,8))
        plt.pie(
            q8['times_prescribed'],
            labels=q8['drug_category'],
            autopct='%1.1f%%'
        )
        plt.title('Drug Category Breakdown')
        plt.show()

    elif choice == '10':
        plt.figure(figsize=(8,8))
        plt.pie(
            q9['total_admissions'],
            labels=q9['admission_type'],
            autopct='%1.1f%%'
        )
        plt.title('Admission Type Analysis')
        plt.show()

    elif choice == '11':
        plt.figure(figsize=(12,6))
        plt.barh(
            q10['drug_name'],
            q10['current_stock']
        )
        plt.title('Low Drug Inventory Alert')
        plt.xlabel('Current Stock')
        plt.tight_layout()
        plt.show()

    else:
        print('Invalid choice. Please enter a number from 0 to 11.')

conn.close()