from PIL import Image #opening,extracting or for pixel data from images,used in line 39
import hashlib #sha256 will be in hashlib
import textwrap #breaking hexadecimal key into small chunks
import cv2 #decomposing into blue green red
import numpy as np
from scipy.integrate import odeint #for chaotic sequences used in line 249
import matplotlib.pyplot as plt 
from bisect import bisect_left as bsearch #indexing sequences generated from chaotic dta
import threading
import os
import json 



''' 
GLOBAL Constants
'''
# Lorenz paramters
a, b, c = 10, 2.667, 28
x0, y0, z0 = 0, 0, 0
tmax, N = 100, 10000 #max time point for generating chaotic sequence,no of points used in integeration of lorenz equations

def lorenz(X, t, a, b, c):
    x, y, z = X
    x_dot = -a*(x - y)
    y_dot = c*x - y - x*z
    z_dot = -b*z + x*y
    return x_dot, y_dot, z_dot


def split_into_rgb_channels(image):
  red = image[:,:,2]
  green = image[:,:,1]
  blue = image[:,:,0]
  return red, green, blue


def securekey (iname):
    img = Image.open(iname)
    m, n = img.size
    print("pixels: {0}  width: {2} height: {1} ".format(m*n, m, n))
    pix = img.load()  #we will get pixel data        
    plainimage = list()                         
    for y in range(n):
        for x in range(m):
            for k in range(0,3):
                plainimage.append(pix[x,y][k])   #for every pixel rgb values are retrieved 
    key = hashlib.sha256()   #hashfunction                   
    key.update(bytearray(plainimage)) # rgb values are updated in plainimage       
    return key.hexdigest() ,m ,n #hexadecimal key 
    #example key 5d6be6940b1aacb90500872672f00876e589cfff951540f65db2f38e31325f8e

def update_lorentz (key): #converts hash into binary and splits binary hash into 32 parts
    key_bin = bin(int(key, 16))[2:].zfill(256)  #key_bin will consist of 256 binary bits 
    k={}                                        
    key_32_parts=textwrap.wrap(key_bin, 8)  #break key_bin into 32 parts each 8 size   
    num=1
    for i in key_32_parts:
        k["k{0}".format(num)]=i
        num = num + 1
    t1 = t2 = t3 = 0
    for i in range (1,12): #xor of t1 with first 11 parts k1 to k11
        t1=t1^int(k["k{0}".format(i)],2) 
        #t1 = 93 ^ 107 ^ 95 ^ 52 ^ 160 ^ 177 ^ 171 ^ 46 ^ 66 ^ 198 ^ 172 (first 11 parts)
    for i in range (12,23):
        t2=t2^int(k["k{0}".format(i)],2)
    for i in range (23,33):
        t3=t3^int(k["k{0}".format(i)],2)   
    global x0 ,y0, z0
    x0=x0 + t1/256            
    y0=y0 + t2/256            
    z0=z0 + t3/256  #t1,t2,t3 194 6 246 x0,y0,z0 x0: 0.7578125 0.0234375 0.9609375          

def decompose_matrix(iname):#reads image data using open cv and splits data into r g b
    image = cv2.imread(iname)#image will contain in bgr sequence
    blue,green,red = split_into_rgb_channels(image)
    for values, channel in zip((red, green, blue), (2,1,0)):
        img = np.zeros((values.shape[0], values.shape[1]), dtype = np.uint8)#empty block img will be created with the size same as the channel being processed
        img[:,:] = (values)
        if channel == 0:
            B = np.asmatrix(img)
        elif channel == 1:
            G = np.asmatrix(img)
        else:
            R = np.asmatrix(img)
    return B,G,R
'''
B: (pixel intensity values)      G:                               R:
[[  0   0   0 ...  63  73  73]   [[139 140 141 ... 184 190 190]   [[213 214 215 ... 227 234 234]
 [  0   0   0 ...  71  81  82]   [140 140 141 ... 184 190 191]   [214 214 215 ... 228 233 234]
 [  0   0   0 ...  77  84  86]   [141 141 142 ... 176 180 182]   [215 215 214 ... 218 222 224]
 ...                            ...                            ...
 [  9  11  14 ...  92  96 101]   [ 20  22  25 ... 155 159 164]   [ 22  24  29 ... 188 190 195]
 [ 14   4   6 ...  85 104 120]   [ 25  15  17 ... 148 165 181]   [ 27  17  21 ... 181 196 212]
 [  8   1   8 ...  90 106 122]]  [ 19  12  19 ... 150 167 183]   [ 21  14  23 ... 186 198 214]]
'''
dna={}
dna["00"]="A"
dna["01"]="T"
dna["10"]="G"
dna["11"]="C"
dna["A"]=[0,0]
dna["T"]=[0,1]
dna["G"]=[1,0]
dna["C"]=[1,1]
#DNA xor
dna["AA"]=dna["TT"]=dna["GG"]=dna["CC"]="A"
dna["AG"]=dna["GA"]=dna["TC"]=dna["CT"]="G"
dna["AC"]=dna["CA"]=dna["GT"]=dna["TG"]="C"
dna["AT"]=dna["TA"]=dna["CG"]=dna["GC"]="T"

def dna_encode(b,g,r): 
    
    b = np.unpackbits(b,axis=1)#converts array of integers to array of its binary values 
    g = np.unpackbits(g,axis=1)
    r = np.unpackbits(r,axis=1)
    '''
        unpacked b:(pixel intensity values are converted to binary)
        [[0 0 0 ... 0 0 1]
        [0 0 0 ... 0 1 0]
        [0 0 0 ... 1 1 0]
        ...
        [0 0 0 ... 1 0 1]
        [0 0 0 ... 0 0 0]
        [0 0 0 ... 0 1 0]]
    '''
    m,n = b.shape
    r_enc= np.chararray((m,int(n/2))) 
    g_enc= np.chararray((m,int(n/2)))
    b_enc= np.chararray((m,int(n/2)))#encodes binary values into dna sequences 
    
    for color,enc in zip((b,g,r),(b_enc,g_enc,r_enc)):
        idx=0
        for j in range(0,m):
            for i in range(0,n,2):
                enc[j,idx]=dna["{0}{1}".format(color[j,i],color[j,i+1])]
                idx+=1
                if (i==n-2):
                    idx=0
                    break
    
    b_enc=b_enc.astype(str)
    g_enc=g_enc.astype(str)
    r_enc=r_enc.astype(str)
    return b_enc,g_enc,r_enc
'''
        Encoded Blue Channel:
        [[b'A' b'A' b'A' ... b'A' b'G' b'T']
        [b'A' b'A' b'A' ... b'T' b'A' b'G']
        [b'A' b'A' b'A' ... b'T' b'T' b'G']
        ...
        [b'A' b'A' b'G' ... b'G' b'T' b'T']
        [b'A' b'A' b'C' ... b'C' b'G' b'A']
        [b'A' b'A' b'G' ... b'C' b'G' b'G']]
'''

def key_matrix_encode(key,b): #creates encoded matrix based on key unlike previous one
    b = np.unpackbits(b,axis=1)#b is passed as parameter just to get size of matrix
    m,n = b.shape
    key_bin = bin(int(key, 16))[2:].zfill(256)
    Mk = np.zeros((m,n),dtype=np.uint8)
    x=0
    for j in range(0,m):
            for i in range(0,n):
                Mk[j,i]=key_bin[x%256]
                x+=1
    
    Mk_enc=np.chararray((m,int(n/2)))
    idx=0
    for j in range(0,m):
        for i in range(0,n,2):
            if idx==(n/2):
                idx=0
            Mk_enc[j,idx]=dna["{0}{1}".format(Mk[j,i],Mk[j,i+1])]
            idx+=1
    Mk_enc=Mk_enc.astype(str)
    return Mk_enc
'''
    Encoded matrix MK_enc:
        [['T' 'T' 'C' ... 'G' 'T' 'G']
        ['G' 'T' 'T' ... 'T' 'G' 'G']
        ['G' 'G' 'C' ... 'A' 'T' 'T']
        ...
        ['A' 'T' 'G' ... 'C' 'G' 'T']
        ['A' 'A' 'T' ... 'A' 'T' 'C']
        ['A' 'G' 'T' ... 'C' 'A' 'A']]

'''

def xor_operation(b,g,r,mk): #xor between encodes bgr and mk which increases more randomness(stronger encryption)
    m,n = b.shape
    bx=np.chararray((m,n))
    gx=np.chararray((m,n))
    rx=np.chararray((m,n))
    b=b.astype(str)
    g=g.astype(str)
    r=r.astype(str)
    """
        b_enc astype(str):              |    mk_enc:
        [['A' 'A' 'A' ... 'A' 'G' 'T']  |   [['T' 'T' 'C' ... 'G' 'T' 'G']
        ['A' 'A' 'A' ... 'T' 'A' 'G']   |    ['G' 'T' 'T' ... 'T' 'G' 'G']
        ['A' 'A' 'A' ... 'T' 'T' 'G']   |    ['G' 'G' 'C' ... 'A' 'T' 'T']
        ...                             |    ...
        ['A' 'A' 'G' ... 'G' 'T' 'T']   |    ['A' 'T' 'G' ... 'C' 'G' 'T']
        ['A' 'A' 'C' ... 'C' 'G' 'A']   |    ['A' 'A' 'T' ... 'A' 'T' 'C']
        ['A' 'A' 'G' ... 'C' 'G' 'G']]  |    ['A' 'G' 'T' ... 'C' 'A' 'A']]

        consider 0,0 ,A and T so AT and dna[AT] is T
    """

    for i in range(0,m):
        for j in range (0,n):
            bx[i,j] = dna["{0}{1}".format(b[i,j],mk[i,j])]
            gx[i,j] = dna["{0}{1}".format(g[i,j],mk[i,j])]
            rx[i,j] = dna["{0}{1}".format(r[i,j],mk[i,j])]
         
    bx=bx.astype(str)
    gx=gx.astype(str)
    rx=rx.astype(str)
    return bx,gx,rx 
'''
    blue final :
        [['T' 'T' 'C' ... 'G' 'C' 'C']
        ['G' 'T' 'T' ... 'A' 'G' 'A']
        ['G' 'G' 'C' ... 'T' 'A' 'C']
        ...
        ['A' 'T' 'A' ... 'T' 'C' 'A']
        ['A' 'A' 'G' ... 'C' 'C' 'C']
        ['A' 'G' 'C' ... 'A' 'G' 'G']]
'''

def gen_chaos_seq(m,n):
    global x0,y0,z0,a,b,c,N
    N=m*n*4
    x= np.array((m,n*4))
    y= np.array((m,n*4))
    z= np.array((m,n*4))
    t = np.linspace(0, tmax, N)   # array of time values ranging from 0 to tmax with n points
    f = odeint(lorenz, (x0, y0, z0), t, args=(a, b, c))    #odeint is for integrating differential eqs
    x, y, z = f.T   #.T is transpose operation so it changes from (N,3)to(3,N)
    x=x[:(N)]       # x [1.44921875 1.4356917  1.42322731 ... 4.04847794 4.0138754  3.97998775]
    y=y[:(N)]
    z=z[:(N)]
    return x,y,z

def plot(x,y,z):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    s = 100
    c = np.linspace(0,1,N)
    for i in range(0,N-s,s):
        ax.plot(x[i:i+s+1], y[i:i+s+1], z[i:i+s+1], color=(1-c[i],c[i],1), alpha=0.4)
    ax.set_axis_off()
    plt.show()

def sequence_indexing(x,y,z):
    #fx stores the indices of sorted x values
    n=len(x)
    fx=np.zeros((n),dtype=np.uint32)
    fy=np.zeros((n),dtype=np.uint32)
    fz=np.zeros((n),dtype=np.uint32)
    seq=sorted(x)
    for k1 in range(0,n):
            t = x[k1]
            k2 = bsearch(seq, t)
            fx[k1]=k2
    seq=sorted(y)
    for k1 in range(0,n):
            t = y[k1]
            k2 = bsearch(seq, t)
            fy[k1]=k2
    seq=sorted(z)
    for k1 in range(0,n):
            t = z[k1]
            k2 = bsearch(seq, t)
            fz[k1]=k2
    return fx,fy,fz
        
def scramble(fx,fy,fz,b,r,g):#scrambles rgb channels
    p,q=b.shape
    size = p*q
    bx=b.reshape(size).astype(str)
    gx=g.reshape(size).astype(str)
    rx=r.reshape(size).astype(str)
    '''
        bx:
            ['A' 'A' 'C' ... 'G' 'C' 'A']
            ['T' 'T' 'C' ... 'A' 'G' 'G']
            ['T' 'A' 'T' ... 'C' 'T' 'T']
    '''
    bx_s=np.chararray((size))
    gx_s=np.chararray((size))
    rx_s=np.chararray((size))
    #based on indices from fx,fy,fz the matrices bx etc will be rearranged 
    for i in range(size):
            idx = fz[i]
            bx_s[i] = bx[idx]
    for i in range(size):
            idx = fy[i]
            gx_s[i] = gx[idx]
    for i in range(size):
            idx = fx[i]
            rx_s[i] = rx[idx]     
    bx_s=bx_s.astype(str)
    
    '''
        bx_s:
          ['T' 'A' 'T' ... 'C' 'T' 'T']
    '''
    gx_s=gx_s.astype(str)
    rx_s=rx_s.astype(str)
    
    b_s=np.chararray((p,q))
    g_s=np.chararray((p,q))
    r_s=np.chararray((p,q))


    b_s=bx_s.reshape(p,q)
    g_s=gx_s.reshape(p,q)
    r_s=rx_s.reshape(p,q)
    return b_s,g_s,r_s

def dna_decode(b,g,r):
    m,n = b.shape
    r_dec= np.ndarray((m,int(n*2)),dtype=np.uint8)
    g_dec= np.ndarray((m,int(n*2)),dtype=np.uint8)
    b_dec= np.ndarray((m,int(n*2)),dtype=np.uint8)
    for color,dec in zip((b,g,r),(b_dec,g_dec,r_dec)):
        for j in range(0,m):
            for i in range(0,n):
                dec[j,2*i]=dna["{0}".format(color[j,i])][0]
                dec[j,2*i+1]=dna["{0}".format(color[j,i])][1]
    b_dec=(np.packbits(b_dec,axis=-1))
    g_dec=(np.packbits(g_dec,axis=-1))
    r_dec=(np.packbits(r_dec,axis=-1))
    return b_dec,g_dec,r_dec



def recover_image(b, g, r, iname, counter):
    img = cv2.imread(iname)
    img[:,:,2] = r
    img[:,:,1] = g
    img[:,:,0] = b

    file_name = os.path.splitext(os.path.basename(iname))[0]
    encrypted_folder = "encryptedimages"

    if not os.path.exists(encrypted_folder):
        os.makedirs(encrypted_folder)

    encrypted_file_path = os.path.join(encrypted_folder, f"encrypted_{file_name}.png")
    cv2.imwrite(encrypted_file_path, img)
    print(f"Saved encrypted image as {encrypted_file_path}")
    return img



def save_encryption_info(file_name, fx, fy, fz, Mk_e, red):
    encryption_info = {
        'fx': fx.tolist(),
        'fy': fy.tolist(),
        'fz': fz.tolist(),
        'Mk_e': Mk_e.tolist(),
        'red': red.tolist()
    }
    return encryption_info




def process_images_in_folder(folder_path, passwords_array):
    threads = []
    counter = 0
    encryption_info = {}
    
    def process_image(file_path, password):
        nonlocal counter
        key, m, n = securekey(file_path)
        update_lorentz(key)
        blue, green, red = decompose_matrix(file_path)
        blue_e, green_e, red_e = dna_encode(blue, green, red)
        Mk_e = key_matrix_encode(key, blue)
        blue_final, green_final, red_final = xor_operation(blue_e, green_e, red_e, Mk_e)
        x, y, z = gen_chaos_seq(m, n)
        fx, fy, fz = sequence_indexing(x, y, z)
        blue_scrambled, green_scrambled, red_scrambled = scramble(fx, fy, fz, blue_final, red_final, green_final)
        b, g, r = dna_decode(blue_scrambled, green_scrambled, red_scrambled)
        img = recover_image(b, g, r, file_path, counter)
        
        encryption_info[password] = {
            'fx': fx.tolist(),
            'fy': fy.tolist(),
            'fz': fz.tolist(),
            'Mk_e': Mk_e.tolist(),
            'red': red.tolist()
        }
        print(f"Image encrypted in Thread {counter}")
        counter += 1

    for file_name, password in passwords_array:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            thread = threading.Thread(target=process_image, args=(file_path, password))
            threads.append(thread)

    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()

    with open("encrypted_data.json", 'w') as info_file:
        json.dump(encryption_info, info_file)

import sys
import subprocess

if __name__ == "__main__":
    if len(sys.argv) > 2:
        folder_path = sys.argv[1]
        passwords_json = sys.argv[2]
        passwords_array = json.loads(passwords_json)
        process_images_in_folder(folder_path, passwords_array)
        subprocess.run(["python", "upload.py"], check=True)
    else:
        print("Please provide a folder path.")