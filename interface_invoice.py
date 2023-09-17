import streamlit as st
import pandas as pd
import os
import zipfile
import shutil
import glob
st.beta_set_page_config(transparent_navbar=True)
if 'data' not in st.session_state:
    st.session_state.data = None

if 'folder' not in st.session_state:
    st.session_state.folder = None

# Streamlit app title and description
st.title("Airplus App")
st.write("Manage invoices by moving and searching for them.")

# Input for source folder path
source_folder_path = st.text_input("Source Folder Path")


# Button to move invoices
if st.button("Move Invoices"):
    try:
        # Create a new folder to move the unzipped files to
        unzipped_folder_path = os.path.join(source_folder_path, "unzipped_invoices")
        if not os.path.isdir(unzipped_folder_path):
            # if the unzipped directory is not present then create it.
            os.makedirs(unzipped_folder_path)
        # Create an excel folder of only xlsx and csv
        excel_folder_path = os.path.join(source_folder_path, "excel_docs")
        if not os.path.isdir(excel_folder_path):
            # if the unzipped directory is not present then create it.
            os.makedirs(excel_folder_path)

        # Create a list of all the files in the zip folder
        zip_files = [f for f in os.listdir(source_folder_path) if f.endswith(".zip")]

        # Create a list of excel files
        excel_files = [f for f in os.listdir(source_folder_path) if f.endswith(('.xlsx', '.csv'))]

        # Move file of XLSX or csv to a specific folder
        for excel_file in excel_files:
            if os.path.exists(os.path.join(source_folder_path, excel_file)):
                st.write(f"File {excel_file} already exists in the destination folder.")
            else:
                shutil.move(os.path.join(source_folder_path, excel_file), excel_folder_path)
                st.write(f"File {excel_file} moved successfully")

        # Unzip each file in the zip folder and move it to the unzipped folder
        for zip_file in zip_files:
            with zipfile.ZipFile(os.path.join(source_folder_path, zip_file)) as zip_ref:
                zip_ref.extractall(unzipped_folder_path)

        # Delete the original zip files
        for zip_file in zip_files:
            os.remove(os.path.join(source_folder_path, zip_file))

            st.success("Invoices moved successfully.")
    except:
        st.error("Please enter a valid path")



# File upload
uploaded_file = st.file_uploader("Upload Invoice Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:

    # Read the uploaded file into a DataFrame
    try:
        if uploaded_file.name.endswith(".csv"):
            airplus_data = pd.read_csv(uploaded_file, encoding='latin-1', sep=';')
        else:
            airplus_data = pd.read_excel(uploaded_file)


        st.success("File loaded successfully.")


        # Display a summary of the DataFrame
        st.subheader("Summary of Invoice Data")
        st.write(airplus_data.head())

        # Input the name of the folder where invoices are to be saved
        st.session_state.folder = st.text_input("Insert the name of the folder to save the invoices of this period")





        # Search for invoices (example: search for a specific invoice)
        if st.button("Search Invoices"):

            if source_folder_path == "":
                st.error("Insert source folder path")
                st.stop()


            # Take the invoice number from the table
            invoices_number = airplus_data[['Positionsnummer', 'Aktionsnummer']] #st.session_state.result = airplus_data
            selected_inv_dir = os.path.join(source_folder_path, st.session_state.folder)

            # Create folder if invoice does not exist
            if not os.path.exists(selected_inv_dir):
                os.makedirs(selected_inv_dir)

            # Take the invoice number from the table
            invoices_number = airplus_data[['Positionsnummer', 'Aktionsnummer']]

            # Create a list for invoices not found
            invoice_found = []
            # Create a loop to go through every invoice number in the file that corresponds to the airplus file
            for index, row in invoices_number.iterrows():  # iterrows is used to establish the index and go per each row of a significant column
                file_name = row['Aktionsnummer']  # design the file name
                value = invoices_number.iloc[index, 0]  # the Value is the position of the invoice
                print(file_name)  # print the file name

                unzipped_folder_path = os.path.join(source_folder_path, "unzipped_invoices")

                found_files = glob.glob(
                    os.path.join(unzipped_folder_path,
                                 f'*{file_name}*'))  # found all the files that contain the file name in unzipped folder
                print(found_files)  # Print the files found
                if found_files:
                    for source_path in found_files:
                        filename = os.path.basename(source_path)
                        new_name = value.astype(str) + "-" + filename  # define the new name
                        destination_path = os.path.join(selected_inv_dir,
                                                        new_name)  # destination path where the new invoices are saved
                        try:
                            # Check the file size
                            file_size = os.path.getsize(source_path)
                            if file_size < 1024:  # 1KB = 1024 bytes
                                print(f"Skipping '{filename}' because its size is less than 1KB.")
                                # invoice_notfound.append(file_name)  # add the file name to the list of not found
                                continue
                            if os.path.exists(destination_path):
                                print(f"File {filename} already exists in the destination folder.")
                                invoice_found.append(file_name)
                            else:
                                shutil.copy(source_path, destination_path)
                                print(f"File {filename} copied to {destination_path}")
                                invoice_found.append(file_name)
                        except FileNotFoundError:
                            print(f"File {filename} not found in source folder")
                    else:
                        print(f"File not found")
                        # invoice_notfound.append(file_name)

            st.success("File copying process completed.")
            print(invoice_found)

            found = pd.DataFrame(invoice_found,
                                 columns=["Invoice"])  # Create a dataframe of invoices that were not found

            # Merge with the detail of the invoices not found
            details_found = airplus_data.merge(found, left_on='Aktionsnummer', right_on='Invoice', how='outer') \
                [['Positionsnummer', 'Invoice', 'Aktionsnummer', 'Bearbeitungsdatum', 'Bruttobetrag', 'Name', 'Routing', \
                  'Leistungserbringer', 'VerkaufsDatum', 'ReiseDatum', 'Auftragsnummer']].sort_values(
                by='Positionsnummer')

            details_notfound = details_found[details_found['Invoice'].isna()].drop(columns=['Invoice'])

            details_notfound['Bruttobetrag'] = pd.to_numeric(details_notfound['Bruttobetrag']\
                                                             .replace(',', '.', regex=True))  # Change data type of bruto amount to price

            print(details_notfound)

            excel_file_path = os.path.join(source_folder_path, "pending_invoice.xlsx")

            if os.path.exists(excel_file_path):
                os.remove(excel_file_path)

            details_notfound.to_excel(excel_file_path, index=False)

            st.success("details of invoices not found   are saved in the source folder path")

    except :
        st.error('Error with search', icon="🚨")




