# TP1: File Transfer Redes(TA048/75.43/75.33/95.60)

## Integrantes:
- Santiago Marczewski - 106404

## Interfaz
### Cliente UPLOAD
```
> python upload.py -h
usage : upload.py [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ]
< command description >
optional arguments :
    -h , -- help        show this help message and exit
    -v , -- verbose     increase output verbosity
    -q , -- quiet       decrease output verbosity
    -H , -- host        server IP address
    -p , -- port        server port
    -s , -- src         source file path
    -n , -- name        file name
    -sr, -- modesr      defines if the mode is stop & wait or selective repeat (default: stop & wait)
```
### Cliente DOWNLOAD
```
> python download.py -h
usage : download.py [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ]
< command description >
optional arguments :
    -h , -- help    show this help message and exit
    -v , -- verbose increase output verbosity
    -q , -- quiet   decrease output verbosity
    -H , -- host    server IP address
    -p , -- port    server port
    -d , -- dst     destination file path
    -n , -- name    file name
    -sr, -- modesr      defines if the mode is stop & wait or selective repeat (default: stop & wait)
```
### Servidor
```
> python start-server.py -h
usage : start-server.py [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s DIRPATH ]
< command description >
optional arguments :
    -h , -- help
    show this help message and exit
    -v , -- verbose     increase output verbosity
    -q , -- quiet       decrease output verbosity
    -H , -- host        service IP address (default: localhost)
    -p , -- port        service port (default: 12000)
    -s , -- storage     storage dir path (default: ./server_storage)
    -sr, -- modesr      defines if the mode is stop & wait or selective repeat (default: stop & wait)
```

### Demo
```
sudo mn -c
sudo python3 ./topologia_demo_sw.py 
sudo python3 ./topologia_demo_sr.py



python3 start-server.py -v -H10.0.0.1 -p12000 -s./server_files -r
python3 upload.py -v -H10.0.0.1 -p12000 -s./client_files -nfile_3.jpg -r
python3 download.py -v -H10.0.0.1 -p12000 -d./client_files -nfile_1.jpg -r
```