'''
Performs a two dimensional affine transform.

@author: Jarno Elonen
'''
import numpy as numpy

def AffineTransform( from_pts, to_pts ):
    """
    Fit an affine transformation to given point sets.
    More precisely: solve (least squares fit) matrix 'A'and 't' from
    'p ~= A*q+t', given vectors 'p' and 'q'.
    Works with arbitrary dimensional vectors (2d, 3d, 4d...).

    Written by Jarno Elonen <elonen@iki.fi> in 2007.
    Placed in Public Domain.

    Based on paper "Fitting affine and orthogonal transformations
    between two sets of points, by Helmuth Spath (2003).
    """

    q = from_pts
    p = to_pts
    if len(q) != len(p) or len(q)<1:
        print "from_pts and to_pts must be of same size."
        return False

    dim = len(q[0]) # num of dimensions
    if len(q) < dim:
        print "Too few points => under-determined system."
        return False

    # Make an empty (dim) x (dim+1) matrix and fill it
    c = [[0.0 for a in range(dim)] for i in range(dim+1)]
    for j in range(dim):
        for k in range(dim+1):
            for i in range(len(q)):
                qt = list(q[i]) + [1]
                c[k][j] += qt[k] * p[i][j]

    # Make an empty (dim+1) x (dim+1) matrix and fill it
    Q = [[0.0 for a in range(dim)] + [0] for i in range(dim+1)]
    for qi in q:
        qt = list(qi) + [1]
        for i in range(dim+1):
            for j in range(dim+1):
                Q[i][j] += qt[i] * qt[j]

    # Ultra simple linear system solver. Replace this if you need speed.
    def gauss_jordan(m, eps = 1.0/(10**10)):
        """Puts given matrix (2D array) into the Reduced Row Echelon Form.
        Returns True if successful, False if 'm' is singular.
        NOTE: make sure all the matrix items support fractions! Int matrix will NOT work!
        Written by Jarno Elonen in April 2005, released into Public Domain"""
        (h, w) = (len(m), len(m[0]))
        for y in range(0,h):
            maxrow = y
            for y2 in range(y+1, h):    # Find max pivot
                if abs(m[y2][y]) > abs(m[maxrow][y]):
                    maxrow = y2
            (m[y], m[maxrow]) = (m[maxrow], m[y])
            if abs(m[y][y]) <= eps:     # Singular?
                pass#return False
            for y2 in range(y+1, h):    # Eliminate column y
                c = m[y2][y] / m[y][y]
                for x in range(y, w):
                    m[y2][x] -= m[y][x] * c
        for y in range(h-1, 0-1, -1): # Backsubstitute
            c  = m[y][y]
            for y2 in range(0,y):
                for x in range(w-1, y-1, -1):
                    m[y2][x] -=  m[y][x] * m[y2][y] / c
            m[y][y] /= c
            for x in range(h, w):       # Normalize row y
                m[y][x] /= c
        return True

    # Augement Q with c and solve Q * a' = c by Gauss-Jordan
    M = [ Q[i] + c[i] for i in range(dim+1)]
    if not gauss_jordan(M):
        print "Error: singular matrix. Points are probably coplanar."
        return False

    # Make a result object
    class Transformation:
        """Result object that represents the transformation
           from affine fitter."""

        def To_Str(self):
            res = ""
            for j in range(dim):
                str = "x%d' = " % j
                for i in range(dim):
                    str +="x%d * %f + " % (i, M[i][j+dim+1])
                str += "%f" % M[dim][j+dim+1]
                res += str + "\n"
            return res

        def Transform(self, pt):
            res = [0.0 for a in range(dim)]
            for j in range(dim):
                for i in range(dim):
                    res[j] += pt[i] * M[i][j+dim+1]
                res[j] += M[dim][j+dim+1]
            return res
    return Transformation()

if __name__ == '__main__':
    #plan_command=[851.0, 784.0, 180.0, 154.0, 813.0, 696.0, 1365.0, 1258.0, 819.0, 771.0, 261.0]
    plan_command=[853.0, 783.0, 0.0, 151.0, 813.0, 695.0, 1368.0, 1262.0, 817.0, 773.0, 257.0]
    #plan_command2=[-853.0, 783.0, 0.0, -1262.0, 817.0, -695.0, 1368.0, -151.0, 813.0, -773.0, 257.0]
    #plan_command=[850.0, 785.0, 0, 153.0, 812.0, 696.0, 1364.0, 1257.0, 818.0, 771.0, 261.0]
    #plan_command=[21.6698, 96.8618, -23.9484,20,15.3722, 92.1386, -4.6377,76.3268, 137.8545, -16.1850,59.9966, 125.6068, -59.2823,26.1272, 100.2123, -62.4344]
    from_pts = ((plan_command[3], plan_command[4]), (plan_command[5], plan_command[6]), (plan_command[7], plan_command[8]))
    to_pts = ((-15.7734,0),(0,15.7734),(15.7734,0)) 
    trn = AffineTransform(from_pts, to_pts)
            
    helicalFiducial=trn.Transform((plan_command[9],plan_command[10])) 
    print "helical:  "+str(helicalFiducial)
    zTarget = -1* (numpy.arctan2(helicalFiducial[1], helicalFiducial[0]) * 180 / numpy.pi) / 180 * 116
    print "Z  "+str(zTarget)
    xyTarget=trn.Transform((plan_command[0],plan_command[1]))
    xyTarget=xyTarget[:2] #disregard Z coordinate which is ultimately figured out by the helical fiducial
    
    print "xy  "+str(xyTarget)
            
    target=xyTarget+[zTarget]+[plan_command[2]]
    print "TARGET:   "+str(target)
    err=0.0
    for i in range(len(from_pts)):
        fp = from_pts[i]
        tp = to_pts[i]
        t = trn.Transform(fp)
        print ("%s => %s ~= %s" % (fp, tuple(t), tp))
        err += ((tp[0] - t[0])**2 + (tp[1] - t[1])**2)**0.5