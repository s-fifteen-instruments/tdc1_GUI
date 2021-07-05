# sfifteen tdc1 GUI (1.1)

INFO

1. This program is a Graphical User Interface (GUI) for s-fifteen intruments' TDC1 Timestamp Device https://s-fifteen.com/products/timestamp.

CONTACT

1. For any bug reports/suggestions, please contact the developer at info@s-fifteen.com or g3.ganjunherng@gmail.com.
2. It would be helpful if you included the error messages printed out to the terminal or whatever program that is catching the errors. (Do not worry if you cannot find this.)

INSTALLATION QUICKSTART

Install the S15lib python package directly with
 
    pip install git+https://github.com/s-fifteen-instruments/pyS15.git

Alternatively you can clone or download the package from https://github.com/s-fifteen-instruments/pyS15.git.
Open a command-line terminal, go into the repository folder and type
  
    pip install -e .
    
1. Full installation instructions at https://github.com/s-fifteen-instruments/pyS15.
2. Other python package requirements: numpy, pyqt5, pyqtgraph, datetime, time. Install with pip or preferred mode of installation.
3. Run tdc1_gui.py with your compiler of choice (This GUI was developed in Visual Studio Code with Python 3.9.2 64-bit).

![image](https://user-images.githubusercontent.com/52197879/124213246-cecf5f80-db22-11eb-932d-57dfb3ce32bd.png)

HOW TO USE

1. Ensure device is connected to PC.
2. Select Device from drop down menu.
![select device](https://user-images.githubusercontent.com/52197879/124435473-9db39100-dda7-11eb-9b19-a08d1fb7be4f.png)

3. Select GUI Mode - singles/pairs. (This is NOT equivalent to the TDC1 mode. For instance the pairs mode uses the TDC1's timestamp mode (3) for its g2 calculations. The modes correspond to the graph tabs - singles:counts, pairs:coincidences.)
![select mode](https://user-images.githubusercontent.com/52197879/124435510-a60bcc00-dda7-11eb-9326-9cf83baca23d.png)

4. Select a Logfile if logging is desired. It is best to write the data to a new, blank Logfile. Leave field empty if not desired.
![select logfile](https://user-images.githubusercontent.com/52197879/124435622-bde35000-dda7-11eb-99d3-430c82e42f75.png)

5. Select Integration time (singles) / acquisition time (pairs) by pressing the arrows or typing in manually.
![select int](https://user-images.githubusercontent.com/52197879/124435863-fdaa3780-dda7-11eb-842f-0510d9d63b86.png)

6. Select Plot Samples. This determines how many data points to display on the graph at once.
![select PLS](https://user-images.githubusercontent.com/52197879/124435788-e703e080-dda7-11eb-976e-f341aad22fca.png)

7. Hit 'Live Start' button.
8. If in Singles mode, select the respective radio buttons to see the plots. 
9. If in Pairs mode, select start and stop channel (Default Start:1, Stop:3), histogram bin width.
10. If in pairs mode, switch to the 'coincidences' tab to view the histogram. The value in the 'Center' spin box allows you to set the center of the histogram display if you already have a rough idea of the expected time delays in your experimental setup.
![image](https://user-images.githubusercontent.com/52197879/124213839-da6f5600-db23-11eb-8de3-9a1dae546236.png)
11. Use mouse to interact with the graph - Click and drag to pan, scroll to zoom, right click for more viewing options.
12. The GUI is under continual development and may bug out if certain buttons are clicked too many times or clicked in unexpected order. Please report any errors to the contact addresses listed at the top of this README. Meanwhile, simply closing and restarting the GUI should fix the errors. These are usually due to certain background flags that have not been set to the right state. Restarting the GUI sets all the flags to their default state and you may begin again from a clean slate.
