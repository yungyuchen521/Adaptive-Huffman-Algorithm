# Huffman Algorithm
### Basic Encoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>b</th>
    <td>1 <= bytes per symbol <= 8</td>
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

### Basic Decoder

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

# Adaptive Huffman Algorithm
### Adaptive Encoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>b</th>
    <td>1 <= bytes per symbol <= 8</td>
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
python adaptive_encoder.py b=1 in=alexnet.pth out=alexnet.pth.comp export=perf.txt
```

### Adaptive Decoder

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

# Improved Adaptive Huffman Algorithm
#### Modifications
Shrink the tree once in a while. Specifically:
1. Split the file into chunks of equal size `K`.
2. Whenever a chunk is fully encoded / decoded, divide the weight of each external node by `alpha`.
3. Update weight of each internal node recursively

**This part is still in progress, there may be some bugs.
For more details, please refer to report.pdf.**


#### Expected Results
- The impact of prior distribution decays exponentially.
- The tree becomes more "adaptive" toward the most recent distribution.

### Improved Adaptive Encoder

<table>
  <tr>
    <th>ARGUMENTS</th>
    <th>DETAIL</th>
    <th>DEFAULT</th>
  </tr>
  <tr>
    <th>b</th>
    <td>1 <= bytes per symbol <= 8</td>
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
    <td>0 <= chunk size (Mb) < 256</td>
    <td>0 (the tree never shrink)</td>
  </tr>
  <tr>
    <th>alpha</th>
    <td>2 <= shrink factor < 256</td>
    <td>2</td>
  </tr>
  <tr>
    <th>export</th>
    <td>export a summary of performance to the given file</td>
    <td>None (do not export)</td>
  </tr>
</table>

#### Sample Command
```shell script
python adaptive_encoder.py b=1 in=alexnet.pth out=alexnet.pth.comp export=perf.txt K=10 alpha=2
```

### Improved Adaptive Decoder
same as `Adaptive Huffman Algorithm`
