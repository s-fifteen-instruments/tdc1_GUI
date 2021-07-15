# sfifteen tdc1 GUI (1.2)

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
3. Run tdc1_funcnew.py with your Python compiler of choice (This GUI was developed in Visual Studio Code with Python 3.9.2 64-bit).

![tdc1 GUI](https://user-images.githubusercontent.com/52197879/125744446-c1e87dc4-7bad-4c2d-92e1-d0aad22e6a4e.png)


HOW TO USE

1. Ensure device is connected to PC.
2. Select Device from drop down menu.
![select device](https://user-images.githubusercontent.com/52197879/125743242-5732c121-e92b-47c1-a0f3-795c76d3afe1.png)


3. Select GUI Mode - singles/pairs. (This is NOT equivalent to the TDC1 mode. For instance the pairs mode uses the TDC1's timestamp mode (3) for its g2 calculations. The modes correspond to the graph tabs - singles:counts, pairs:coincidences.)
![select mode](https://user-images.githubusercontent.com/52197879/125743271-b7decbf9-0b53-49d6-9d52-a14b408ac217.png)


4. Select a Logfile if logging is desired. It is best to write the data to a new, blank Logfile. Leave field empty if not desired.
![select logfile](https://user-images.githubusercontent.com/52197879/125743281-6deff07e-6b41-4577-919f-e1eaf6def9cd.png)


5. Select Integration time (singles) / acquisition time (pairs) by pressing the arrows or typing in manually then hitting enter.
![select int](https://user-images.githubusercontent.com/52197879/125743293-5a772701-c621-4e8d-826e-7f4b92b341b7.png)


6. Select Plot Samples. This determines how many data points to display on the graph at once.
![select PLS](https://user-images.githubusercontent.com/52197879/125743318-82824e87-a36e-49c5-a2dc-a6a3dd8249d2.png)

7. The timer checkbox can be selected for a finite experiment runtime.
![select timer](https://user-images.githubusercontent.com/52197879/125743523-d6fb2db6-9a5b-4685-8c38-4306e65c1348.png)


8. Hit 'Live Start' button.
9. If in Singles mode, select the respective radio buttons to see the plots.
![select singles](https://user-images.githubusercontent.com/52197879/125743782-23614597-6510-447f-aa90-b8ac12c0d554.png)


10. If in Pairs mode, select start and stop channel (Default Start:1, Stop:3), histogram bin width.
![Select pairs](https://user-images.githubusercontent.com/52197879/125743807-aa69677b-c575-46ae-8f92-dc42a3dd29a2.png)

11. If in pairs mode, switch to the 'coincidences' tab to view the histogram. The value in the 'Stop Ch offset' spinbox allows you to set a software delay for coincidence counting.
![image](https://user-images.githubusercontent.com/52197879/124213839-da6f5600-db23-11eb-8de3-9a1dae546236.png)

12. Use mouse to interact with the graph - Click and drag to pan, scroll to zoom, right click for more viewing options.
13. Right clicking on the graph and clicking on 'export...' brings up an options window for exporting the graph.
![export options](https://user-images.githubusercontent.com/52197879/125744126-8405c494-2602-48dc-b9ad-fd294ba0b8f3.png)

14. To begin a new round of data collection, click the 'Clear Data' button on the respective graphs.

15. The GUI is under continual development and may bug out if certain buttons are clicked too many times or clicked in unexpected order. Please report any errors to the contact addresses listed at the top of this README. Meanwhile, simply closing and restarting the GUI should fix the errors. These are usually due to certain background flags that have not been set to the right state. Restarting the GUI sets all the flags to their default state and you may begin again from a clean slate.
