import cv2
import numpy as np
import pandas as pd
import math


def threshold_binary_inv(im, t):
    """
    All pixels with intensity < t become 255
    and the rest become 0
    """
    
    _, im_t = cv2.threshold(im, t, 255, cv2.THRESH_BINARY_INV)
    return im_t


def threshold_binary(im, t):
    """
    All pixels with intensity > t become 255
    and the rest become 0
    """
    
    _, im_t = cv2.threshold(im, t, 255, cv2.THRESH_BINARY)
    return im_t


def apply_region_mask(image, region_vertices):

    mask = np.zeros_like(image)
    cv2.fillPoly(mask, region_vertices, 255)

    return cv2.bitwise_and(image, mask)


def mask_threshold_range(im, thresh_min, thresh_max):
    """
    Return a binary mask image where pixel intensities
    of the original image lie within [thresh_min, thresh_max)
    """

    binary_output = (im >= thresh_min) & (im < thresh_max)
    return np.uint8(binary_output)


def bitwise_or(images):
    """
    Apply bitwise OR operation to a list of images
    """

    assert len(images) > 0

    if len(images) == 1:
        return images[0]

    res = cv2.bitwise_or(images[0], images[1])
    if len(images) == 2:
        return res

    for im in images[2:]:
        res = cv2.bitwise_or(res, im)

    return res


def crop_rectangle(im, x0, y0, w, h):

    x1 = x0 + w
    y1 = y0 + h

    return im[y0:y1, x0:x1]


def find_ccomp(im, *args, **kwargs):
    """
    Finds connected components in a binary image.
    Returns the label image and a Pandas data frame
    with the connected components' statistics.

    *args and **kwargs are forwarded to the
    cv2.connectedComponentsWithStats call
    """

    num, labels, stats, centroids = cv2.connectedComponentsWithStats(im, *args, **kwargs)
    
    stats_df = pd.DataFrame(stats, columns=['left', 'top', 'width', 'height', 'area'])
    stats_df['x'] = centroids[:,0]
    stats_df['y'] = centroids[:,1]
    
    return labels, stats_df


def ccomp_bbox_subimage(im, stats, i):
    """
    Crop a subimage corresponding to a 
    single connected component.

    i - integer-location index in the stats data frame 
    (to be used with iloc)
    """

    left, top = stats.iloc[i].left, stats.iloc[i].top
    w, h = stats.iloc[i].width, stats.iloc[i].height
    return im[int(top):int(top+h), int(left):int(left+w)]


def fill_holes_based_on_contours(im_input):
    """
    Fill holes inside an object in a binary image
    using cv2.findContours.

    An object is characterized by white color (255),
    while the background is black (0)

    See example of this technique at:
    https://stackoverflow.com/questions/10316057/filling-holes-inside-a-binary-object
    """

    im_out, contour, _ = cv2.findContours(im_input, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contour:
        cv2.drawContours(im_out, [cnt], 0, 255, -1)

    return im_out


def gather_masked_pixels(im, mask):
    """
    For an image and the mask, 
    gather all pixels that 
    belong to the mask as a 1D array
    """

    mask = mask.astype(np.bool)
    values = im[mask]

    return values


def region_ellipse_from_moments(im_binary):
    """
    Estimate equivalent ellipse from binary image moments.

    Returns:
    center_x, center_y -- x and y coordinates of the ellipse center (center og gravity)
    d1, d2 -- larger and smaller diameters of the ellipse
    theta -- angle between x axis and the d1

    A nice tutorial:
    http://raphael.candelier.fr/?blog=Image%20Moments
    """
    
    m = cv2.moments(im_binary, binaryImage=True)
    
    area = m['m00']

    center_x = m['m10'] / area
    center_y = m['m01'] / area
    
    mu20 = m['mu20'] / area
    mu02 = m['mu02'] / area
    mu11 = m['mu11'] / area
    
    s = np.sqrt((mu20 - mu02)**2 + 4 * mu11**2)
    d1 = 2 * np.sqrt(2 * (mu20 + mu02 + s))
    d2 = 2 * np.sqrt(2 * (mu20 + mu02 - s))
    
    theta = 0.5 * math.atan(2 * mu11 / (mu20 - mu02))
    
    if mu20 < mu02:
        theta += math.pi/2
        
    return center_x, center_y, d1, d2, theta