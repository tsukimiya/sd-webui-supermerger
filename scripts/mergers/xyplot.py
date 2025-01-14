import random
import copy
from PIL import Image
from modules import images
from modules.shared import opts
from scripts.mergers.mergers import types,smerge,simggen,filenamecutter,draw_origin,wpreseter
from scripts.mergers.model_util import usemodelgen

hear = False
hearm = False

state_mergen = False

numadepth = []

def freezetime():
    global state_mergen
    state_mergen = True

def numanager(normalstart,xtype,xmen,ytype,ymen,
                    weights_a,weights_b,model_a,model_b,model_c,alpha,beta,mode,useblocks,custom_name,save_sets,id_sets,wpresets,
                    prompt,nprompt,steps,sampler,cfg,seed,w,h):
    global numadepth
    grids = []
    if normalstart:
        result,currentmodel,xyimage,a,b,c= sgenxyplot(xtype,xmen,ytype,ymen,
                                                                             weights_a,weights_b,model_a,model_b,model_c,alpha,beta,mode,useblocks,custom_name,save_sets,id_sets,wpresets,
                                                                             prompt,nprompt,steps,sampler,cfg,seed,w,h)
        if xyimage is not None:grids =[xyimage[0]]
        else:print(result)
    else:
        if numadepth ==[]:
            return "no reservation",*[None]*5
        result=currentmodel=xyimage=a=b=c = None

    while True:
        for i,row in enumerate(numadepth):
            if row[1] =="waiting":  
                numadepth[i][1] = "Operating"
                try:
                    result,currentmodel,xyimage,a,b,c = sgenxyplot(*row[2:])
                except Exception as e:
                    print(e)
                    numadepth[i][1] = "Error"
                else:
                    if xyimage is not None:
                        grids.append(xyimage[0])
                        numadepth[i][1] = "Finished"
                    else:
                        print(result)
                        numadepth[i][1] = "Error"
        wcounter = 0
        for row in numadepth:
            if row[1] != "waiting":
                wcounter += 1
        if wcounter == len(numadepth):
            break

    return result,currentmodel,grids,a,b,c

def numaker(xtype,xmen,ytype,ymen,
#msettings=[weights_a,weights_b,model_a,model_b,model_c,alpha,beta,mode,useblocks,custom_name,save_sets,id_sets,wpresets]       
                    weights_a,weights_b,model_a,model_b,model_c,alpha,beta,mode,useblocks,custom_name,save_sets,id_sets,wpresets,
                    prompt,nprompt,steps,sampler,cfg,seed,w,h):
    global numadepth
    numadepth.append([len(numadepth)+1,"waiting",xtype,xmen,ytype,ymen,
                    weights_a,weights_b,model_a,model_b,model_c,alpha,beta,mode,useblocks,custom_name,save_sets,id_sets,wpresets,
                    prompt,nprompt,steps,sampler,cfg,seed,w,h])
    return numalistmaker(copy.deepcopy(numadepth))

def nulister(redel):
    global numadepth
    if redel == False:
        return numalistmaker(copy.deepcopy(numadepth))
    if redel ==-1:
        numadepth = []
    else:
        try:del numadepth[int(redel-1)]
        except Exception as e:print(e)
    return numalistmaker(copy.deepcopy(numadepth))

def numalistmaker(numa):
    if numa ==[]: return [["no data","",""],]
    for i,r in enumerate(numa):
        r[2] =  types[int(r[2])]
        r[4] =  types[int(r[4])]
        numa[i] = r[0:6]+r[8:11]+r[12:16]+r[6:8]
    return numa

def caster(news,hear):
    if hear: print(news)

def sgenxyplot(xtype,xmen,ytype,ymen,
                    weights_a,weights_b,model_a,model_b,model_c,alpha,beta,mode,useblocks,custom_name,save_sets,id_sets,wpresets,
                    prompt,nprompt,steps,sampler,cfg,seed,w,h):
    global hear
    #type[0:none,1:aplha,2:beta,3:seed,4:mbw,5:model_A,6:model_B,7:model_C,8:pinpoint ]
    xtype = types[xtype]
    ytype = types[ytype]

    modes=["Weight" ,"Add" ,"Triple","Twice","Diff"]
    xs=ys=0
    weights_a_in=weights_b_in="0"

    def castall(hear):
        if hear :print(f"xmen:{xmen}, ymen:{ymen}, xtype:{xtype}, ytype:{ytype}, weights_a:{weights_a_in}, weights_b:{weights_b_in}, model_A:{model_a},model_B :{model_b}, model_C:{model_c}, alpha:{alpha},\
        beta :{beta}, mode:{mode}, blocks:{useblocks}")

    pinpoint = "pinpoint" in xtype or "pinpoint" in ytype
    usebeta = modes[2] in mode or modes[3] in mode

    #check and adjust format
    print(f"XY plot start, mode:{mode}, X: {xtype}, Y: {ytype}, MBW: {useblocks}")
    castall(hear)
    None5 = [None,None,None,None,None]
    if xmen =="": return "ERROR: parameter X is empty",*None5
    if ymen =="" and not ytype=="none": return "ERROR: parameter Y is empty",*None5
    if model_a ==[] and not ("model_A" in xtype or "model_A" in ytype):return f"ERROR: model_A is not selected",*None5
    if model_b ==[] and not ("model_B" in xtype or "model_B" in ytype):return f"ERROR: model_B is not selected",*None5
    if model_c ==[] and usebeta and not ("model_C" in xtype or "model_C" in ytype):return "ERROR: model_C is not selected",*None5
    if xtype == ytype: return "ERROR: same type selected for X,Y",*None5

    if useblocks:
        weights_a_in=wpreseter(weights_a,wpresets)
        weights_b_in=wpreseter(weights_b,wpresets)

    #for X only plot, use same seed
    if seed == -1: seed = int(random.randrange(4294967294))

    #for XY plot, use same seed
    def dicedealer(zs):
        for i,z in enumerate(zs):
            if z =="-1": zs[i] = str(random.randrange(4294967294))
        print(f"the die was thrown : {zs}")

    #adjust parameters, alpha,beta,models,seed: list of single parameters, mbw(no beta):list of text,mbw(usebeta); list of pair text
    def adjuster(zmen,ztype):
        if "mbw" in ztype:#men separated by newline
            zs = zmen.splitlines()
            caster(zs,hear)
            if usebeta:
                zs = [zs[i:i+2] for i in range(0,len(zs),2)]
                caster(zs,hear)
        else:
            zs = [z.strip() for z in zmen.split(',')]
            caster(zs,hear)
        if "seed" in ztype:dicedealer(zs)
        return zs

    xs = adjuster(xmen,xtype)
    ys = adjuster(ymen,ytype)

    #in case beta selected but mode is Weight sum or Add or Diff
    if ("beta" in xtype or "beta" in ytype) and not usebeta:
        mode = modes[3]
        print(f"{modes[3]} mode automatically selected)")

    #in case mbw or pinpoint selected but useblocks not chekced
    if ("mbw" in xtype or "pinpoint" in xtype) and not useblocks:
        useblocks = True
        print(f"MBW mode enabled")

    if ("mbw" in ytype or "pinpoint" in ytype) and not useblocks:
        useblocks = True
        print(f"MBW mode enabled")

    xyimage=[]
    xcount =ycount=0
    allcount = len(xs)*len(ys)

    #for STOP XY bottun
    flag = False
    global state_mergen
    state_mergen = False

    #type[0:none,1:aplha,2:beta,3:seed,4:mbw,5:model_A,6:model_B,7:model_C,8:pinpoint ]
    blockid=["BASE","IN00","IN01","IN02","IN03","IN04","IN05","IN06","IN07","IN08","IN09","IN10","IN11","M00","OUT00","OUT01","OUT02","OUT03","OUT04","OUT05","OUT06","OUT07","OUT08","OUT09","OUT10","OUT11"]
    #format ,IN00 IN03,IN04-IN09,OUT4,OUT05
    def weightsdealer(x,xtype,y,weights):
        caster(f"weights from : {weights}",hear)
        zz = x if "pinpoint" in xtype else y
        za = y if "pinpoint" in xtype else x
        zz = [z.strip() for z in zz.split(' ')]
        weights_t = [w.strip() for w in weights.split(',')]
        if zz[0]!="NOT":
            flagger=[False]*26
            changer = True
        else:
            flagger=[True]*26
            changer = False
        for z in zz:
            if z =="NOT":continue
            if "-" in z:
                zt = [zt.strip() for zt in z.split('-')]
                if  blockid.index(zt[1]) > blockid.index(zt[0]):
                    flagger[blockid.index(zt[0]):blockid.index(zt[1])+1] = [changer]*(blockid.index(zt[1])-blockid.index(zt[0])+1)
                else:
                    flagger[blockid.index(zt[1]):blockid.index(zt[0])+1] = [changer]*(blockid.index(zt[0])-blockid.index(zt[1])+1)
            else:
                flagger[blockid.index(z)] =changer    
        for i,f in enumerate(flagger):
            if f:weights_t[i]=za
        outext = ",".join(weights_t)
        caster(f"weights changed: {outext}",hear)
        return outext

    def abdealer(z):
        if " " in z:return z.split(" ")[0],z.split(" ")[1]
        return z,z

    def xydealer(z,zt):
        nonlocal alpha,beta,seed,weights_a_in,weights_b_in,model_a,model_b,model_c
        if pinpoint:return
        if "and" in zt:
            alpha,beta = abdealer(z)
            return
        if "alpha" in zt:alpha = z
        if "beta" in zt: beta = z
        if "seed" in zt:seed = int(z)
        if "mbw" in zt:
            def weightser(z):return z, z.split(',',1)[0]
            if usebeta:
                weights_a_in,alpha = weightser(wpreseter(z[0],wpresets))
                weights_b_in,beta = weightser(wpreseter(z[1],wpresets))
            else:
                weights_a_in,alpha = weightser(wpreseter(z,wpresets))
        if "model_A" in zt:model_a = z
        if "model_B" in zt:model_b = z
        if "model_C" in zt:model_c = z

    # plot start
    for y in ys:
        xydealer(y,ytype)
        xcount = 0
        for x in xs:
            xydealer(x,xtype)
            if ("alpha" in xtype or "alpha" in ytype) and pinpoint:
                weights_a_in = weightsdealer(x,xtype,y,weights_a)
                weights_b_in = weights_b
            if ("beta" in xtype or "beta" in ytype) and pinpoint:
                weights_b_in = weightsdealer(x,xtype,y,weights_b)
                weights_a_in =weights_a
            print(f"XY plot: X: {xtype}, {str(x)}, Y: {ytype}, {str(y)} ({xcount+ycount*len(xs)+1}/{allcount})")
            if not (xtype=="seed" and xcount > 0):
               _ , currentmodel,modelid,theta_0=smerge(weights_a_in,weights_b_in, model_a,model_b,model_c, float(alpha),float(beta),mode,useblocks,"","",id_sets,False) 
               usemodelgen(theta_0,model_a)
                             # simggen(prompt, nprompt, steps, sampler, cfg, seed, w, h,mergeinfo="",id_sets=[],modelid = "no id"):
            image_temp=simggen(prompt, nprompt, steps, sampler, cfg, seed, w, h,currentmodel,id_sets,modelid)
            xyimage.append(*image_temp[0])
            xcount+=1
            if state_mergen:
                flag = True
                break
        ycount+=1
        if flag:break

    if flag and ycount ==1:
        xs = xs[:xcount]
        ys = [ys[0],]
        print(f"stopped at x={xcount},y={ycount}")
    elif flag:
        ys=ys[:ycount]
        print(f"stopped at x={xcount},y={ycount}")

    if "mbw" in xtype and usebeta: xs = [f"alpha:({x[0]}),beta({x[1]})" for x in xs ]
    if "mbw" in ytype and usebeta: ys = [f"alpha:({y[0]}),beta({y[1]})" for y in ys ]

    xs[0]=xtype+" = "+xs[0] #draw X label
    if ytype!=types[0] or "model" in ytype:ys[0]=ytype+" = "+ys[0]  #draw Y label

    if ys==[""]:ys = [" "]

    gridmodel= makegridmodelname(model_a, model_b,model_c, useblocks,mode,xtype,ytype,alpha,beta,weights_a,weights_b,usebeta)
    grid = smakegrid(xyimage,xs,ys,gridmodel,image_temp[4])

    xyimage.insert(0,grid)

    state_mergen = False
    return "Finished",currentmodel,xyimage,*image_temp[1:4]

def smakegrid(imgs,xs,ys,currentmodel,p):
    ver_texts = [[images.GridAnnotation(y)] for y in ys]
    hor_texts = [[images.GridAnnotation(x)] for x in xs]

    w, h = imgs[0].size
    grid = Image.new('RGB', size=(len(xs) * w, len(ys) * h), color='black')

    for i, img in enumerate(imgs):
        grid.paste(img, box=(i % len(xs) * w, i // len(xs) * h))

    grid = images.draw_grid_annotations(grid,int(p.width), int(p.height), hor_texts, ver_texts)
    grid = draw_origin(grid, currentmodel,w*len(xs),h*len(ys),w)
    if opts.grid_save:
        images.save_image(grid, opts.outdir_txt2img_grids, "xy_grid", extension=opts.grid_format, prompt=p.prompt, seed=p.seed, grid=True, p=p)

    return grid

def makegridmodelname(model_a, model_b,model_c, useblocks,mode,xtype,ytype,alpha,beta,wa,wb,usebeta):
    model_a=filenamecutter(model_a)
    model_b=filenamecutter(model_b)
    model_c=filenamecutter(model_c)

    if not usebeta:beta,wb = "not used","not used"
    vals = ""
    modes=["Weight" ,"Add" ,"Triple","Twice"]

    if "mbw" in xtype:
        wa = "X"
        if usebeta:wb = "X"

    if "mbw" in ytype:
        wa = "Y"
        if usebeta:wb = "Y"

    wa = "alpha = " + wa
    wb = "beta = " + wb

    x = 50
    while len(wa) > x:
        wa  = wa[:x] + '\n' + wa[x:]
        x = x + 50

    x = 50
    while len(wb) > x:
        wb  = wb[:x] + '\n' + wb[x:]
        x = x + 50

    if "model" in xtype:
        if "A" in xtype:model_a = "model A"
        elif "B" in xtype:model_b="model B"
        elif "C" in xtype:model_c="model C"

    if "model" in ytype:
        if "A" in ytype:model_a = "model A"
        elif "B" in ytype:model_b="model B"
        elif "C" in ytype:model_c="model C"

    if modes[1] in mode:
        currentmodel =f"{model_a} \n {model_b} - {model_c})\n x alpha"
    elif modes[2] in mode:
        currentmodel =f"{model_a} x \n(1-alpha-beta) {model_b} x alpha \n+ {model_c} x beta"
    elif modes[3] in mode:
        currentmodel =f"({model_a} x(1-alpha) \n + {model_b} x alpha)*(1-beta)\n+  {model_c} x beta"
    else:
        currentmodel =f"{model_a} x (1-alpha) \n {model_b} x alpha"

    if "alpha" in xtype:alpha = "X"
    if "beta" in xtype:beta = "X" 
    if "alpha" in ytype:alpha = "Y"
    if "beta" in ytype:beta = "Y"

    if "mbw" in xtype:
        alpha = "X"
        if usebeta:beta = "X"

    if "mbw" in ytype:
        alpha = "Y"
        if usebeta:beta = "Y"

    vals = f"\nalpha = {alpha},beta = {beta}" if not useblocks else f"\n{wa}\n{wb}"

    currentmodel = currentmodel+vals
    return currentmodel