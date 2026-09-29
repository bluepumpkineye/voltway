"""Door cards.

A door card is the body's own flank moved inward by a thickness that varies
with height, split into bands between boundary curves in side elevation:

    y(x, z) = skin_y(x, z) - thickness(z) - proud(band)

    card = DoorCard(loft, x_front(z), x_rear(z), z_bottom, z_top(x), thickness)
    card.band(name, z_lo(x), z_hi(x), mat, proud=0.0, x0=None, x1=None)
    card.armrest(name, x0, x1, z, ...)      a padded shelf swept along x
    card.path(pts_xz, lift)                 a surface path for piping/handles

Bands are separate meshes with their own `proud` offset, so a raised insert
shows a real step at its edge (put piping on it) and the seams read as seams.
Built on the LEFT side (+Y) and mirrored unless told otherwise.
"""
import math

from mathutils import Vector

from .. import mesh as M
from .sweep import Sweep, grid_mesh, tube, ellipse, smooth_path


class DoorCard:
    def __init__(self, loft, x_front, x_rear, z_bottom, z_top, thickness, v_top=None,
                 side=1.0):
        """x_front(z), x_rear(z): the card's fore/aft edges at height z;
        z_top(x): its top edge (the belt); thickness(z): skin-to-card depth.
        v_top: highest section parameter to search the skin in (the belt)."""
        self.loft = loft
        self.xf, self.xr = x_front, x_rear
        self.zb, self.zt = z_bottom, z_top
        self.th = thickness
        self.v_top = v_top if v_top is not None else loft.V_SHOULDER + 0.03
        self.side = side

    def skin_y(self, x, z):
        L = self.loft
        v = L.v_at_z(x, z, 0.02, self.v_top)
        return L.section_v(x, v)[0]

    def point(self, x, z, proud=0.0):
        y = self.skin_y(x, z) - self.th(z) - proud
        return (x, self.side * y, z)

    def band(self, name, collection, mat, z_lo, z_hi, proud=0.0, x0=None, x1=None,
             nx=56, nz=10, edge_round=0.004, mirror=True):
        """A panel between z_lo(x) and z_hi(x), from x0(z) to x1(z) (defaults:
        the card's own ends). Its edges roll back by edge_round so a proud
        band reads as an upholstered panel, not a sheet."""
        x0 = x0 or self.xr
        x1 = x1 or self.xf
        rows = []
        for i in range(nx + 1):
            t = i / float(nx)
            col = []
            for j in range(nz + 1):
                s = j / float(nz)
                # solve x and z together: x limits depend on z, z limits on x
                x = x0(0.5) + (x1(0.5) - x0(0.5)) * t if callable(x0) else x0
                for _ in range(4):
                    zl, zh = z_lo(x), z_hi(x)
                    z = zl + (zh - zl) * s
                    xa, xb = x0(z), x1(z)
                    x = xa + (xb - xa) * t
                rows_in = min(j, nz - j, i, nx - i)          # grid rows from the edge
                roll = edge_round * max(0.0, 1.0 - rows_in / 2.0)
                col.append(self.point(x, z, proud - roll))
            rows.append(col)
        ob = grid_mesh(name, rows, collection, mat)
        M.orient(ob.data, lambda c: (0.0, -self.side, 0.0))
        if mirror:
            M.mirror_y(ob)
        return ob

    def carrier(self, name, collection, mat, z_lo, z_hi, x0=None, x1=None, back=0.012,
                nx=40, nz=12, mirror=True):
        """The black moulded carrier behind the upholstered bands. Every seam
        between bands is a V where two edges roll back; without a carrier
        each seam shows a hairline of the painted door behind it."""
        ob = self.band(name, collection, mat, z_lo, z_hi, proud=-back, x0=x0, x1=x1,
                       nx=nx, nz=nz, edge_round=0.0, mirror=False)
        # A flange all round, from the carrier's edge out to 6 mm inside the
        # skin: the card becomes a closed box, so a ray through any slot at
        # its edges (the B-pillar shut line, the front hinge side) meets
        # black trim instead of running on behind the card to the paint.
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.edges.ensure_lookup_table()
        boundary = [e for e in bm.edges if e.is_boundary]
        outer = {}
        for e in boundary:
            for v in e.verts:
                if v not in outer:
                    x, y, z = v.co
                    yo = self.side * (self.skin_y(x, z) - 0.006)
                    outer[v] = bm.verts.new((x, yo, z))
        for e in boundary:
            a, b = e.verts
            bm.faces.new((a, b, outer[b], outer[a]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        bm.to_mesh(ob.data)
        bm.free()
        M.orient(ob.data, lambda c: (0.0, -self.side, 0.0))
        if mirror:
            M.mirror_y(ob)
        return ob

    def belt_cap(self, name, collection, mat, x0, x1, z_top, glass_gap=-0.001, nx=48,
                 mirror=True):
        """The window-sill cap along the card's top edge, out to the glass.

        The card stands 5-7 cm inboard of the skin at the belt; without a cap
        you look straight down that slot into the painted door shell (the
        magenta leak renders, carkit.qa: every exterior surface seen from the
        cabin is a bug)."""
        prof = [(0.0, -0.002), (0.18, 0.004), (0.55, 0.006), (0.88, 0.004),
                (1.0, 0.0), (1.0, -0.022)]
        rows = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / float(nx)
            zt = z_top(x)
            y_in = self.skin_y(x, zt - 0.002) - self.th(zt - 0.002) + 0.004
            y_out = self.skin_y(x, zt) - glass_gap
            rows.append([(x, self.side * (y_in + (y_out - y_in) * a), zt + dz)
                         for (a, dz) in prof])
        ob = grid_mesh(name, rows, collection, mat)
        M.orient(ob.data, lambda c: (0.0, 0.0, 1.0))
        if mirror:
            M.mirror_y(ob)
        return ob

    def curve(self, pts_xz, proud=0.0, n=40):
        """A path on the card through side-elevation points."""
        path = smooth_path([(x, 0.0, z) for (x, z) in pts_xz], n)
        return [self.point(p[0], p[2], proud) for p in path]

    def armrest(self, name, collection, mat, x0, x1, z, width=0.070, height=0.050,
                n=40, mirror=True):
        """A padded shelf along the card from x0 to x1, top at z. Its ends
        taper into the card."""
        spine = [(x0 + (x1 - x0) * k / 10.0, 0.0, z) for k in range(11)]

        def section(i, s):
            e = min(1.0, min(s, 1.0 - s) * 7.0)             # tapered ends
            e = e * e * (3 - 2 * e)
            w = 0.004 + (width - 0.004) * e
            y0 = self.skin_y(x0 + (x1 - x0) * s, z) - self.th(z)
            # (a, b): a = inward from the card face (toward the cabin), b = up
            return [(0.0, -height), (w * 0.55, -height * 0.92), (w * 0.95, -height * 0.55),
                    (w, -0.012), (w * 0.9, -0.002), (w * 0.55, 0.0), (0.0, -0.003)], y0
        pts = []
        for k in range(n + 1):
            s = k / float(n)
            x = x0 + (x1 - x0) * s
            prof, y0 = section(k, s)
            from .sweep import cr_segments
            sec = cr_segments(prof, 4)
            pts.append([(x, self.side * (y0 - a), z + b) for (a, b) in sec])
        ob = grid_mesh(name, pts, collection, mat)
        M.orient(ob.data, lambda c: (0.0, -self.side, 0.4))
        if mirror:
            M.mirror_y(ob)
        return ob
