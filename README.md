# Adaptive-Huffman-Algorithm

## Environment
- python 3.8.2
- MacOS Monterey

## Basic Encoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>b</th>
    <td>bytes per symbol</td>
    <td>must be provided</td>
  </tr>
  <tr>
    <th>in</th>
    <td>file to be compressed</td>
    <td>must be provided</td>
  </tr>
  <tr>
    <th>out</th>
    <td>path of the output file</td>
    <td>"{in}.comp"</td>
  </tr>
  <tr>
    <th>export</th>
    <td>export a summary of performance to the given file</td>
    <td>None (do not export)</td>
  </tr>
</table>

#### Sample Command
```shell script
python encoder.py b=1 in=alexnet.pth out=alexnet.pth.comp export=perf.txt
```

## Basic Decoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>in</th>
    <td>file to be decompressed</td>
    <td>must be provided</td>
  </tr>
  <tr>
    <th>out</th>
    <td>path of the output file</td>
    <td>"{in}.decomp"</td>
  </tr>
</table>

#### Sample Command
```shell script
python decoder.py in=alexnet.pth.comp out=alexnet.pth.decomp
```

## Adaptive Encoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>b</th>
    <td>bytes per symbol</td>
    <td>must be provided</td>
  </tr>
  <tr>
    <th>in</th>
    <td>file to be compressed</td>
    <td>must be provided</td>
  </tr>
  <tr>
    <th>out</th>
    <td>path of the output file</td>
    <td>"{in}.comp"</td>
  </tr>
   <tr>
    <th>K</th>
    <td>chunk size</td>
    <td>0 (the tree never shrink)</td>
  </tr>
  <tr>
    <th>alpha</th>
    <td>shrink factor</td>
    <td>2</td>
  </tr>
  <tr>
    <th>export</th>
    <td>export a summary of performance to the given file</td>
    <td>None (do not export)</td>
  </tr>
</table>
For details about chunk size & shrink factor, please refer to the report

#### Sample Command
```shell script
python adaptive_encoder.py b=1 in=alexnet.pth out=alexnet.pth.comp export=perf.txt K=10 alpha=2
```

## Adaptive Decoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>in</th>
    <td>file to be decompressed</td>
    <td>must be provided</td>
  </tr>
  <tr>
    <th>out</th>
    <td>path of the output file</td>
    <td>"{in}.decomp"</td>
  </tr>
</table>

#### Sample Command
```shell script
python adaptive_decoder.py in=alexnet.pth.comp out=alexnet.pth.decomp
```