def trimoutercircle( sky ) :
    x1trim = 300
    x2trim = 2280
    # Determine the dim en si on s o f the image
    width = sky.shape[0]
    height = sky.shape[ 1 ]
    centeronwidth = int(width/2)
    centeronheight = int(height/2)
    circleradius = 971
    #Trim the pixels around the sky
    skycircle = np.zeros((width, height), dtype=np.uint8)
    rr,cc = draw.circle(
            centeronwidth,centeronheight,circleradius
            )
    skycircle[rr,cc] = 1
    skytrimmed = sky.copy( )
    skytrimmed[skycircle == 0 ]= 0
    return skytrimmed[:,x1trim : x2trim]
    # Convenience f u n c ti o n t h a t l o a d s an image
    # and t rim s the o u t e r c i r c l e
def loadandtrim(filename):
    sky = io.imread(filename)
    skytrimmed = trimoutercircle(sky)
    return skytrimmed
    # P r o c e s s an image by d i v i d i n g the red ch annel
    # by the bl u e ch annel
def processimagerbratio(skytrimmed):
    ratio =(
        skytrimmed[...,0]/skytrimmed[...,2]
        )
    # This v al u e was de te rmined by tunin g
    threshold=0.9
    ratio[ratio>threshold] = 255
    ratio[ratio<=threshold] = 0
    # Apply a median f i l t e r t o smooth ed g e s
    return median(ratio,disk(10))
    # Determine the p e r c e n t a g e o f the sky c o v e r e d
    # by cl o u d s by c o u n ti n g p i x e l s
def calculatecloudcover(image,pixelsincircle):
    white = 255
    # image i s c u r r e n t l y a 2D a r ray , c o n v e r t t o 1D
    flattenedimage = image.flatten( )
    whitepixels = np.sum(flattenedimage == white)
    # White p i x e l s den o te a r e a s where
    # cl o u d s have been d e t e c t e d
    cloudpercentage=(
            whitepixels/pixelsincircle*100
            )
    return cloudpercentage
# Convenience method t o c om pl e t el y p r o c e s s
# an image from i t s f i l e p a t h
def cloudcoverfromimage(imagepath, pixelsincircle):
    image = loadandtrim(imagepath)
    rbrimage = processimagerbratio(image)
    coverage = calculatecloudcover(
            rbrimage, pixelsincircle
            )
    return coverage
# P r o c e s s an image and s a ve i t
def processandsaveimage(targetdate, filename):
    image = loadandtrim(filename)
    outfile = targetdate + ’−’ + filename
    rbroutputfilename=(
                settings.rbroutputdirectory+outfile
                )
    rbrimage = processimagerbratio(image)
    io.imsave(rbroutputfilename,rbrimage)
    rbdiffoutputfilename = (
            settings.rbdiffoutputdirectory+outfile
            )
    rbdiffimage=processimagerbdifference(image)
    io.imsave(rbdiffoutputfilename,rbdiffimage)
   
# P r o c e s s a l l the images i n a d i r e c t o r y
def processdirectory(targetdate, targetdatadirectory):
    skyimagefilenames = [
        f for f in listdir(targetdatadirectory)
            if is file (join(targetdatadirectory, f))
            ]
    for skyimagefilename in skyimagefilenames:
        processandsaveimage(
            targetdate,
            targetdatadirectory+skyimagefilename)
        print(”Completed: ”+skyimagefilename)
def createcoveragetuple(imagepath , pixelsincircle) :
    # s t r i p f i l e e x t e n si o n
    timestr= imagepath.parts[−1].split(’.’)[0]
    try:
        coverage=cloudcoverfromimage(
        imagepath,pixelsincircle
    )
    #Create a tuple of local timestamp
    #and cloud coverage
    result =(timestr, coverage)
    return result
    except ValueError:
        return None
        
def estimatecompletiontime(directorypath, completed):
    processtime  = 1
    imagecount = len(listdir(directorypath)) − completed
    hourconversion = 3600
    estimatedtime = (
        processtime * imagecount/hourconversion
        )
    print(”Remaining time {0} hours.Completed {1}”. format(
        estimatedtime,completed))
        
def cloudcoveragefromdirectory(directorypath):
    circleradius= 971
    pixelsincircle= int(np.pi*(circleradius ** 2))
    coverages = []
    images = listdir(directorypath)
    images.sort()
    for i, file in enumerate(images):
        filepath = Path(str(directorypath)+”/”+file)
        if i%50 == 0:
            estimatecompletiontime(directorypath,i)
            savecoverages(coverages,i)
            coverages = [ ]
        coverage=createcoveragetuple(
                filepath,pixelsincircle
                )
        coverages.append(coverage)
    p r i n t ( ” Fi ni s h e d ” )

def savecoverages(coverages,i):
    pst = pytz.timezone(”America/LosAngeles”)
    clouddf= pd.DataFrame(
        coverages,columns =[”Date”, ”Cloud Coverage”]
            )
    clouddf.Date = pd.todatetime(clouddf.Date , utc=True)
    clouddf.setindex(” Date ” , inplace=True)
    clouddf[”Cloud Coverage”] = pd.tonumeric(
            clouddf[”Cloud Coverage”]
            )
    # S o r t by the time inde x
    clouddf = clouddf.sortindex( )
    # I n t e r p o l a t e t o a minute f r e q u e n c y
    clouddf=clouddf.reindex(
        clouddf.index.tzconvert(pst)
        )
    # Export da ta f rame
    clouddf.index=clouddf.index.strftime(
        ’%Y−%m−%d %H:%M:%S ’
        )
    clouddf.index.name= ”Date ”
    clouddf.tocsv(’coverage{0}.csv’.format(i))


