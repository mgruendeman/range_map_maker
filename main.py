from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QComboBox, QListWidget, QListWidgetItem, QCheckBox, QRadioButton
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
import requests
import json
# from concurrent.futures import ThreadPoolExecutor
from services.gbif_service import GBIFService
from services.plotting_service import PlottingService
import threading
import os
import cartopy.crs as ccrs

class RangePlotterApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Range Plotter')
        self.initUI()
        self.gbif_service = GBIFService()
        self.plotting_service = PlottingService()


    def initUI(self):
        self.species_box = self.build_species_inputs_box()
        self.map_params_box = self.build_map_paramaters_box()
        self.plot_box = self.build_plot_groupbox()

        layout = QGridLayout(self)
        layout.addWidget(self.species_box, 0, 0)
        layout.addWidget(self.map_params_box, 1, 0)
        layout.addWidget(self.plot_box, 1, 1)


    def build_species_inputs_box(self):

        species_input_box = QGroupBox()
        layout = QGridLayout()

        genus_label = QLabel()
        genus_label.setText("Genus: ")

        genus_input = QLineEdit()
        genus_input.setText("Puma")

        
        species_label = QLabel()
        species_label.setText("Species: ")

        species_input = QLineEdit()
        species_input.setText('concolor')
        
        license_combo_box = QComboBox()
        license_combo_box.addItem("CC0 - No Rights Reserved", "CC0_1_0")
        license_combo_box.addItem("CC-BY - Attribution", "CC_BY_4_0")
        license_combo_box.addItem("CC-BY-NC - Attribution-NonCommercial", "CC_BY_NC_4_0")

        license_list_widget = QListWidget()
        license_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        licenses = [
            ("CC0 - No Rights Reserved", "CC0_1_0"),
            ("CC-BY - Attribution", "CC_BY_4_0"),
            ("CC-BY-NC - Attribution - NonCommercial", "CC_BY_NC_4_0")
        ]

        checkboxes = []
        row = 2
        for text, data in licenses:
            checkbox = QCheckBox(text)
            checkbox.setProperty("licenseData", data)  # Custom property to hold the license data
            layout.addWidget(checkbox, row, 0, 1, 2)  
            checkboxes.append(checkbox)
            row += 1


        download_data_button = QPushButton()
        download_data_button.setText("Download Data")
        download_data_button.clicked.connect(
            lambda: self.download_data(
                genus_input.text(), 
                species_input.text(),
                checkboxes
            )
        )


        
        layout.addWidget(genus_label,0,0,1,1)
        layout.addWidget(genus_input,0,1,1,1)
        layout.addWidget(species_label,1,0,1,1)
        layout.addWidget(species_input,1,1,1,1)
        layout.addWidget(download_data_button,6,0,1,2)


        species_input_box.setLayout(layout)

        return species_input_box


    def build_map_paramaters_box(self):

        max_lat_label = QLabel()
        max_lat_label.setText("Max Latitude: ")

        self.max_lat_entry = QLineEdit()
        self.max_lat_entry.setText("67")
        

        min_lat_label = QLabel()
        min_lat_label.setText("Min Latitude: ")

        self.min_lat_entry = QLineEdit()
        self.min_lat_entry.setText("15")
        

        max_long_label = QLabel()
        max_long_label.setText("Max Longitude: ")

        self.max_long_entry = QLineEdit()
        self.max_long_entry.setText("-25")

        min_long_label = QLabel()
        min_long_label.setText("Min Longitude: ")

        self.min_long_entry = QLineEdit()
        self.min_long_entry.setText("-165")


        smooth_fact_label = QLabel()
        smooth_fact_label.setText("Smooth Factor: ")

        self.smooth_fact_entry = QLineEdit()
        self.smooth_fact_entry.setText("0.1")

        eps_label = QLabel()
        eps_label.setText("Epsilon: ")

        self.eps_entry = QLineEdit()
        self.eps_entry.setText("4")
        self.eps_entry.setToolTip("Epsion is the maximum distance between two samples for them to be considered as in the same neighborhood. Too small an epsilon value can lead to data points not being clustered at all (most points will be considered noise). Too large an epsilon can cause separate clusters to merge and not enough granularity in the clustering.")


        num_points_label = QLabel()
        num_points_label.setText("Num Points: ")

        num_points_entry = QLineEdit()

        species_label = QLabel()
        species_label.setText("Species: ")    

        self.species_combobox = QComboBox()
        self.populate_combobox_with_directories(self.species_combobox, "./data")

        points_checkbox_label = QLabel()
        points_checkbox_label.setText("Plot Observation Points: ")    

        self.points_checkbox = QCheckBox("", self)

        outline_checkbox_label = QLabel()
        outline_checkbox_label.setText("Plot Outline: ")    

        self.outline_checkbox = QCheckBox("", self)


        styling_header_label = QLabel()
        styling_header_label.setText("Styling: ")

        style_point_size_label = QLabel()
        style_point_size_label.setText("Point Size: ")

        self.style_point_size_entry = QLineEdit()
        self.style_point_size_entry.setText("1")


        style_point_color_label = QLabel()
        style_point_color_label.setText("Point Size: ")

        self.style_point_color_entry = QLineEdit()
        self.style_point_color_entry.setText("#0B6A00")

        fill_range_checkbox_label = QLabel()
        fill_range_checkbox_label.setText("Fill Range: ")    

        self.fill_range_checkbox = QCheckBox("", self)

        range_outline_size_label = QLabel()
        range_outline_size_label.setText("Range Outline Size: ")

        self.range_outline_size_entry = QLineEdit()
        self.range_outline_size_entry.setText("1")





        map_paramaters_box = QGroupBox()
        map_paramaters_box.setTitle("Graph Paramaters")

        layout = QGridLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(species_label,0,0)
        layout.addWidget(self.species_combobox,0,1)
        layout.addWidget(min_lat_label,2,0)
        layout.addWidget(max_lat_label,1,0)
        layout.addWidget(min_lat_label,2,0)
        layout.addWidget(max_long_label,3,0)
        layout.addWidget(min_long_label,4,0)
        layout.addWidget(self.max_lat_entry,1,1)
        layout.addWidget(self.min_lat_entry,2,1)
        layout.addWidget(self.max_long_entry,3,1)
        layout.addWidget(self.min_long_entry,4,1)
        layout.addWidget(smooth_fact_label,5,0)
        layout.addWidget(self.smooth_fact_entry,5,1)
        layout.addWidget(eps_label,6,0)
        layout.addWidget(self.eps_entry,6,1)
        layout.addWidget(num_points_label,7,0)
        layout.addWidget(num_points_entry,7,1)
        layout.addWidget(points_checkbox_label,8,0)
        layout.addWidget(self.points_checkbox,8,1)
        layout.addWidget(outline_checkbox_label,9,0)
        layout.addWidget(self.outline_checkbox,9,1)
        layout.addWidget(styling_header_label,10,0,2,2)
        layout.addWidget(style_point_size_label,12,0)
        layout.addWidget(self.style_point_size_entry,12,1)
        layout.addWidget(style_point_color_label,13,0)
        layout.addWidget(self.style_point_color_entry,13,1)

        layout.addWidget(fill_range_checkbox_label,14,0)
        layout.addWidget(self.fill_range_checkbox,14,1)
        layout.addWidget(range_outline_size_label,15,0)
        layout.addWidget(self.range_outline_size_entry,15,1)




        map_paramaters_box.setLayout(layout)


        return map_paramaters_box

    def list_directories(self,path):
        """List all directories within a given path."""
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    def populate_combobox_with_directories(self,combo_box, path):
        """Populate the given QComboBox with directory names from the specified path."""
        directories = self.list_directories(path)
        for directory in directories:
            combo_box.addItem(directory)


    def build_plot_groupbox(self):


        plot_box = plot_box = QGroupBox()

        self.fig = Figure(figsize=(15, 15), dpi=500)

        self.canvas = FigureCanvas(self.fig)


        ## TODO: Put this in plotting paramaters probably

        btn_update_plot = QPushButton('Update Plot')
        btn_update_plot.clicked.connect(self.update_plot)


        layout = QGridLayout()
        
        layout.addWidget(btn_update_plot)
        layout.addWidget(self.canvas)


        plot_box.setLayout(layout)  

        # layout.addWidget()

        return plot_box


    def update_plot(self,fig):

        # TODO add check that long and lat entries are set
        # TODO strip long and lat entries

        self.fig.clf()

        ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        

        self.plotting_service.plot_data(
            self.points_checkbox.isChecked(),
            self.outline_checkbox.isChecked(),
            os.path.join('data',self.species_combobox.currentText(),self.species_combobox.currentText()+".json"),
            ax,
            float(self.eps_entry.text()),
            float(self.smooth_fact_entry.text()),
            float(self.style_point_size_entry.text()),
            self.style_point_color_entry.text(),
            self.fill_range_checkbox.isChecked(),
            float(self.range_outline_size_entry.text()),
        )

        ax.set_extent([self.min_long_entry.text(),self.max_long_entry.text(),self.min_lat_entry.text(),self.max_lat_entry.text()])
        

        self.canvas.draw()


    def download_data(self, genus,species,checkboxes):
        ## TODO: Make check for licsenses, if none are selected warn user



        licenses = self.get_selected_licenses(checkboxes)

        # if len(licenses) == 0:


        gbif_service = GBIFService()

        thread = threading.Thread(target=gbif_service.download_gbif_data, args=(genus, species, 'json',licenses))
        thread.start()


    def get_selected_licenses(self, checkboxes):
        """Collects and returns a comma-separated string of selected licenses."""
        selected_licenses = [checkbox.property("licenseData") for checkbox in checkboxes if checkbox.isChecked()]
        return ','.join(selected_licenses)
        
    




    def species_edit_finished():




        pass









def main():
    app = QApplication(sys.argv)
    window = RangePlotterApp()
    window.show()
    sys.exit(app.exec())





if __name__ == '__main__':
    main()



