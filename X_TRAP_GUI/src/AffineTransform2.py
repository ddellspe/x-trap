'''
Created on Jun 15, 2012

@author: Collin & David
'''
import numpy as np
from numpy import linalg
from operator import itemgetter

def AffineTransform2( from_pts, to_pts ):
    """
    Note that both P and A are 2x3 matrices instead of 3x3 because adding the 
    additional "dummy" row is superfluous.
    """
    
    # check that there are match points
    if len(from_pts) != len(to_pts) or len(to_pts)<1:
        print "from_pts and to_pts must be of same size."
        return False

    # check the dimensions
    dim = len(from_pts[0]) # num of dimensions
    if len(from_pts) < dim:
        print "Too few points => under-determined system."
        return False
    elif len(from_pts) > dim + 1:
        print "Too many points => over-determined system."
        return False

    
    #segregate the x and y coordinages
    from_pts_x, from_pts_y = zip(*from_pts)
    to_pts_x, to_pts_y = zip(*to_pts)
    
    #create the Matricies for processing
    I = np.matrix([from_pts_x, from_pts_y, [1,1,1]])
    P = np.matrix([to_pts_x, to_pts_y])
    
    #Calculate the 2D affine transform matrix (A)
    A = P * linalg.pinv(I) 

    # Make a result object
    class Transformation:
        """Result object that represents the transformation
           from affine fitter."""

        def To_Str(self):
            res = ""
            for j in range(dim):
                str1 = "x%d' = " % j
                for i in range(dim):
                    str1 +="x%d * %f + " % (i, A[i][j+dim+1])
                str1 += "%f" % A[dim][j+dim+1]
                res += str1 + "\n"
            return res

        def Transform(self, pt_x, pt_y):
            pt_vector = np.matrix([[pt_x], [pt_y], [1]])
            transformed_pt = A * pt_vector
            return map(itemgetter(0), transformed_pt.tolist())
    return Transformation()
    
    
if __name__ == '__main__':
    #plan_command=[851.0, 784.0, 180.0, 154.0, 813.0, 696.0, 1365.0, 1258.0, 819.0, 771.0, 261.0]
    plan_command=[853.0, 783.0, 0.0, 151.0, 813.0, 695.0, 1368.0, 1262.0, 817.0, 773.0, 257.0]
    #plan_command=[-853.0, 783.0, 0.0, -1262.0, 817.0, -695.0, 1368.0, -151.0, 813.0, -773.0, 257.0]
    #plan_command=[850.0, 785.0, 0, 153.0, 812.0, 696.0, 1364.0, 1257.0, 818.0, 771.0, 261.0]
    #plan_command=[21.6698, 96.8618, -23.9484,20,15.3722, 92.1386, -4.6377,76.3268, 137.8545, -16.1850,59.9966, 125.6068, -59.2823,26.1272, 100.2123, -62.4344]
    from_pts = ((plan_command[3], plan_command[4]), (plan_command[5], plan_command[6]), (plan_command[7], plan_command[8]))
    to_pts = ((-15.7734,0),(0,15.7734),(15.7734,0)) 
    trn = AffineTransform2(from_pts, to_pts)
            
    helicalFiducial=trn.Transform(*plan_command[9:11]) 
    print "helical:", helicalFiducial
    zTarget = -1 * (np.arctan2(helicalFiducial[1], helicalFiducial[0]) * 180 / np.pi) / 180 * 116
    print "Z:", str(zTarget)
    xyTarget=trn.Transform(*plan_command[:2])
    
    print "xy:", xyTarget
            
    target = xyTarget + [zTarget, plan_command[2]]
    print "TARGET:", target
    err=0.0
    for i in range(len(from_pts)):
        fp = from_pts[i]
        tp = to_pts[i]
        t = trn.Transform(*fp)
        print ("%s => %s ~= %s" % (fp, tuple(t), tp))
        err += ((tp[0] - t[0])**2 + (tp[1] - t[1])**2)**0.5