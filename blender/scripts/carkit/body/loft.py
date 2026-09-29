"""The master surface of a car's flank: a loft of sections along x.

A car's side is not one fair curve. It has a hard shoulder crease where the door
surface turns up into the glass, a tucked sill, and a hip over the arches. So a
section here is TWO centripetal Catmull-Rom segments that meet at the shoulder
with independent tangents - that corner is the character line. Below it the
section runs floor -> sill -> lower-door undercut -> hip -> upper door ->
shoulder; above it, beltline step -> tumblehome -> roof rail (or, ahead of the
cowl, the fender crown) -> roof centre.

Surface parameterisation
------------------------
    S(x, v)   x = station along the car in metres, +X forward
              v = 0 at the underbody centreline, 1 at the roof centreline,
                  v_shoulder at the crease

Every section control point comes from a PROFILE CURVE of x - that is the
whole description of a car's body:

    z_roof      top centreline: nose, hood, screen, roof, deck, tail
    z_floor     underbody
    y_hip       half-width at the widest point (over the arches)
    z_hip       height of that widest point
    z_shoulder  the beltline crease
    y_shoulder  its half-width
    y_roof      half-width of the roof rail, or of the fender crowns
    y_rocker    sill outer face
    undercut    concavity of the lower door (metres, 0 = flat)
    z_crest     rail height above/below the centreline (twin crowns > 0,
                wraparound screen < 0)

The shape of the section between those points is a recipe with a handful of
style constants (Section); the SU7 values are the defaults. `crease="soft"`
makes the shoulder tangent-continuous for cars without a sharp beltline.
"""
import math

from ..geom import catmull_rom


class Section:
    """Style constants of the section recipe. Defaults: SU7 Ultra.

    Distances in metres; fractions are of the span named.
    """

    def __init__(self, **kw):
        # keep the section well-ordered where the profiles crowd each other
        self.shoulder_above_hip = 0.030
        self.shoulder_below_roof = 0.045
        self.hip_above_rocker = 0.020
        self.hip_below_shoulder = 0.025
        # lower section
        self.floor_flat = 0.60            # floor runs flat to this fraction of the sill
        self.floor_rise = 0.002
        self.floor_edge = (0.030, 0.012)  # (in from sill, up from floor)
        self.sill_face = (0.004, 0.062)
        self.undercut_z = 0.40            # undercut height, fraction sill -> hip
        self.upper_door = (0.72, 0.009, 0.62)   # (y blend, y tuck, z fraction hip -> shoulder)
        # upper section
        self.step_max = 0.032             # beltline step above the crease
        self.step_ratio = 0.30            # ... limited to this share of the headroom
        self.step_in = 0.014
        self.tumble = (0.60, 0.40, 0.56, 0.40)   # (y shoulder share, y rail share, z head share, crest share)
        self.rail_in = 0.52               # inboard point between rail and centreline
        self.rail_crest = 0.34
        # greenhouse inset (LoftBody y_glass), unused without it: the tumble
        # point moves in by this share of the extra inset at the glass base
        self.glass_mid = 0.35
        # hood domes (LoftBody z_dome / y_dome), unused without them
        self.dome_groove = 0.35           # groove depth, share of the dome's rise
        self.dome_flank = (0.55, 0.30)    # inner flank point: (y share, height share)
        for k, v in kw.items():
            if not hasattr(self, k):
                raise AttributeError("unknown section constant: " + k)
            setattr(self, k, v)


class LoftBody:
    """A car's flank surface from its profile curves.

    Attribute names are the SU7 module's (FRONT_AXLE, Z_ROOF, ...) so a
    LoftBody and the old su7_surface module are interchangeable.
    """

    def __init__(self, *, length, width, height, front_axle, rear_axle,
                 wheel_r, arch_r, z_roof, z_floor, y_hip, z_hip, z_shoulder,
                 y_shoulder, y_roof, y_rocker, undercut, z_crest,
                 v_shoulder=0.520, cowl_x=None, backlight_x=None,
                 sill_height=0.150, n_lower=44, n_upper=40, core_z=0.62,
                 crease="sharp", section=None, name="body", z_dome=None, y_dome=None,
                 y_glass=None, z_step=None, soft=None):
        self.name = name
        self.LENGTH, self.WIDTH, self.HEIGHT = length, width, height
        self.HALF_L = length / 2.0
        self.HALF_W = width / 2.0
        self.FRONT_AXLE, self.REAR_AXLE = front_axle, rear_axle
        self.WHEEL_R, self.ARCH_R = wheel_r, arch_r
        self.V_SHOULDER = v_shoulder
        self.COWL_X, self.BACKLIGHT_X = cowl_x, backlight_x
        self.Z_ROOF, self.Z_FLOOR = z_roof, z_floor
        self.Y_HIP, self.Z_HIP = y_hip, z_hip
        self.Z_SHOULDER, self.Y_SHOULDER = z_shoulder, y_shoulder
        self.Y_ROOF, self.Y_ROCKER = y_roof, y_rocker
        self.UNDERCUT, self.Z_CREST = undercut, z_crest
        self.sill_height = sill_height
        self.n_lower, self.n_upper = n_lower, n_upper
        self.core_z = core_z
        if crease not in ("sharp", "soft"):
            raise ValueError("crease must be 'sharp' or 'soft'")
        self.crease = crease
        # Optional second crown inboard of the rail/fender crown: a dome on
        # the hood (the Luxeed RX: domes at y ~0.58 either side of a low
        # centre, the fender crowns at ~0.79 outboard of the hood's shut
        # lines). Z_DOME is its height over Z_ROOF; None or <= 0 = no dome.
        self.Z_DOME, self.Y_DOME = z_dome, y_dome
        # Optional greenhouse base half-width: where it is inside the plain
        # step (shoulder - step_in), the glass/pillar starts that far in, on a
        # wider shoulder deck, and the tumble point follows by k.glass_mid of
        # the extra. A cabin tapering rearward on broad haunches (the Luxeed
        # RX: the rear door glass and C-pillar ~20 cm inside the shoulder).
        self.Y_GLASS = y_glass
        # Optional, per station: the step's rise above the crease (replacing
        # the recipe's k.step_max) and how soft the crease is (0 = the sharp
        # corner, 1 = tangent-continuous, blended between). Behind the Luxeed
        # RX's rear doors the crisp beltline crease becomes a rounded haunch
        # with a deck sloping up to the C-pillar: a crease at the doors' height
        # there built a flat shelf that hid the mirrors from behind.
        self.Z_STEP, self.SOFT = z_step, soft
        self.k = section or Section()
        self._section_cache = {}
        self._split_cache = {}
        self._rail_cache = {}

    # ----------------------------------------------------------- profiles
    PROFILES = ("Z_ROOF", "Z_FLOOR", "Y_HIP", "Z_HIP", "Z_SHOULDER", "Y_SHOULDER",
                "Y_ROOF", "Y_ROCKER", "UNDERCUT", "Z_CREST")

    def profiles(self):
        return {n: getattr(self, n) for n in self.PROFILES}

    def z_rocker(self, x):
        """Height of the top of the side sill."""
        return self.Z_FLOOR(x) + self.sill_height

    # ------------------------------------------------------------ sections
    def section(self, x, n_lower=None, n_upper=None):
        """Half-section at station x as [(y, z), ...] from underbody to roof centre.

        Index `split(x)` is the shoulder crease. Sampled finely and memoised:
        section_v interpolates linearly along this polyline, so a coarse one
        leaves facets that near-mirror glazing turns into interference bands,
        and section_v is called once per grid vertex.
        """
        n_lower = self.n_lower if n_lower is None else n_lower
        n_upper = self.n_upper if n_upper is None else n_upper
        key = (round(x, 4), n_lower, n_upper)
        hit = self._section_cache.get(key)
        if hit is not None:
            return hit
        k = self.k
        zf, zh, zs = self.Z_FLOOR(x), self.Z_HIP(x), self.Z_SHOULDER(x)
        yh, ys, yr, yrf = self.Y_HIP(x), self.Y_SHOULDER(x), self.Y_ROCKER(x), self.Y_ROOF(x)
        zr = self.z_rocker(x)
        zroof = self.Z_ROOF(x)

        zs = min(max(zs, zh + k.shoulder_above_hip), zroof - k.shoulder_below_roof)
        zh = min(max(zh, zr + k.hip_above_rocker), zs - k.hip_below_shoulder)

        # The concave undercut between the sill and the hip is measured against
        # the straight line joining them, so it stays a concavity wherever the
        # sill and hip move to.
        und = self.UNDERCUT(x)
        zu = zr + (zh - zr) * k.undercut_z
        t_u = (zu - zr) / max(1e-4, zh - zr)
        yu = (yr + (yh - yr) * t_u) - und
        yb, tuck, zfrac = k.upper_door
        lower = [
            (0.0, zf),
            (yr * k.floor_flat, zf + k.floor_rise),        # flat floor
            (yr - k.floor_edge[0], zf + k.floor_edge[1]),  # floor edge rolling up
            (yr - k.sill_face[0], zf + k.sill_face[1]),    # sill outer face
            (yr, zr),                                      # top of the sill
            (yu, zu),                                      # lower-door undercut
            (yh, zh),                                      # hip - widest point
            (min(yh, ys + (yh - ys) * yb) - tuck,
             zh + (zs - zh) * zfrac),                      # upper door
            (ys, zs),                                      # shoulder crease
        ]
        # The beltline step scales with the headroom above the crease: a fixed
        # step overshoots where the shoulder runs close under the hood and the
        # section folds back on itself (a crumple down the fender).
        head = max(0.0, zroof - zs)
        step = min(k.step_max, head * k.step_ratio)
        if self.Z_STEP is not None:
            step = min(max(step, self.Z_STEP(x)), head * 0.5)
        crest = self.Z_CREST(x)
        z_rail = zroof + crest
        ts, tr, th, tc = k.tumble
        yb0 = ys - k.step_in
        yb = yb0 if self.Y_GLASS is None else min(yb0, self.Y_GLASS(x))
        upper = [
            (ys, zs),
            (yb, zs + step),                               # step above the crease
            (ys * ts + yrf * tr - (yb0 - yb) * k.glass_mid,
             zs + head * th + crest * tc),
            (yrf, z_rail),                                 # roof rail / fender crown
            (yrf * k.rail_in, zroof + crest * k.rail_crest),
            (0.0, zroof),
        ]
        if self.Z_DOME is not None:
            # three inboard points instead of two, easing from points on the
            # plain section (no dome) to the dome as it grows, so the dome
            # fades in without a crease where it starts
            dome = max(0.0, self.Z_DOME(x))
            a = min(1.0, dome / 0.010)
            a = a * a * (3.0 - 2.0 * a)
            yd = min(self.Y_DOME(x), yrf - 0.06)
            p0 = (yrf * k.rail_in, zroof + crest * k.rail_crest)
            p1 = (yrf * k.rail_in * 0.5, zroof + crest * k.rail_crest * 0.30)
            q = (0.5 * (yrf + p0[0]), 0.5 * (z_rail + p0[1]))
            # the groove between the fender crown and the dome, where the
            # hood's shut line runs, k.dome_groove of the dome's rise below
            # the lower of the two; the dome's inner flank drops to
            # k.dome_flank[1] of its rise by k.dome_flank[0] x its y
            yv = 0.5 * (yrf + yd)
            zv = min(z_rail, zroof + dome) - k.dome_groove * dome
            d0 = (yd, zroof + dome)                        # the hood's dome
            d1 = (yd * k.dome_flank[0], zroof + dome * k.dome_flank[1])

            def ease(p, d):
                return (p[0] + (d[0] - p[0]) * a, p[1] + (d[1] - p[1]) * a)
            upper[-2:] = [ease(q, (yv, zv)), ease(p0, d0), ease(p1, d1),
                          (0.0, zroof)]                    # the valley between
        soft = 1.0 if self.crease == "soft" else 0.0
        if self.SOFT is not None:
            soft = min(1.0, max(0.0, self.SOFT(x)))
        if soft >= 1.0:
            lo_pts = catmull_rom(lower, n_lower, tail=upper[1])
            up_pts = catmull_rom(upper, n_upper, head=lower[-2])
        else:
            lo_pts = catmull_rom(lower, n_lower)
            up_pts = catmull_rom(upper, n_upper)
            if soft > 0.0:
                # both are resampled to the same counts: blend point by point
                lo_s = catmull_rom(lower, n_lower, tail=upper[1])
                up_s = catmull_rom(upper, n_upper, head=lower[-2])
                lo_pts = [(a[0] + (b[0] - a[0]) * soft, a[1] + (b[1] - a[1]) * soft)
                          for a, b in zip(lo_pts, lo_s)]
                up_pts = [(a[0] + (b[0] - a[0]) * soft, a[1] + (b[1] - a[1]) * soft)
                          for a, b in zip(up_pts, up_s)]
        out = lo_pts + up_pts[1:]
        self._split_cache[key] = len(lo_pts) - 1
        # Catmull-Rom accelerates outward on the segment approaching the hip
        # even with a vertical tangent there; normalising the section's peak
        # back onto y_hip is a ~1.5 % scale - invisible in shape, exact in width.
        ymax = max(p[0] for p in out)
        if ymax > yh > 1e-6:
            s = yh / ymax
            out = [(p[0] * s, p[1]) for p in out]
        if len(self._section_cache) > 40000:
            self._section_cache.clear()
        self._section_cache[key] = out
        return out

    def split(self, x, n_lower=None, n_upper=None):
        """Index of the shoulder crease in section(x)."""
        n_lower = self.n_lower if n_lower is None else n_lower
        n_upper = self.n_upper if n_upper is None else n_upper
        return self._split_cache.get((round(x, 4), n_lower, n_upper), n_lower)

    def section_v(self, x, v, n_lower=None, n_upper=None):
        """Sample the section at normalised parameter v in [0, 1]."""
        n_lower = self.n_lower if n_lower is None else n_lower
        n_upper = self.n_upper if n_upper is None else n_upper
        pts = self.section(x, n_lower, n_upper)
        n = len(pts)
        # map v so that v_shoulder lands exactly on the crease vertex
        k_sh = self._split_cache.get((round(x, 4), n_lower, n_upper), n_lower)
        V = self.V_SHOULDER
        if v <= V:
            f = (v / V) * k_sh
        else:
            f = k_sh + ((v - V) / (1.0 - V)) * (n - 1 - k_sh)
        i = int(math.floor(f))
        i = max(0, min(n - 2, i))
        t = f - i
        y0, z0 = pts[i]
        y1, z1 = pts[i + 1]
        return (y0 + (y1 - y0) * t, z0 + (z1 - z0) * t)

    def surface(self, x, v):
        """A point on the half body surface, as (x, y, z) with y >= 0."""
        y, z = self.section_v(x, v)
        return (x, y, z)

    # -------------------------------------------------------- wheel arches
    def arch_top_z(self, x):
        """Height of the wheel-arch opening at station x, or None if clear of it."""
        for axle in (self.FRONT_AXLE, self.REAR_AXLE):
            dx = x - axle
            if abs(dx) < self.ARCH_R:
                return self.WHEEL_R + math.sqrt(max(0.0, self.ARCH_R * self.ARCH_R - dx * dx))
        return None

    def arch_v(self, x, v_floor=0.02, hi=None, iters=26):
        """Section parameter of the wheel arch at station x, or None clear of it."""
        hi = self.V_SHOULDER if hi is None else hi
        for axle in (self.FRONT_AXLE, self.REAR_AXLE):
            dx = x - axle
            if abs(dx) >= self.ARCH_R:
                continue
            h = math.sqrt(max(0.0, 1.0 - (dx / self.ARCH_R) ** 2))
            z_arch = self.WHEEL_R + self.ARCH_R * h
            if self.section_v(x, hi)[1] < z_arch:
                return None                   # arch would swallow the shoulder
            a, b = v_floor, hi
            for _ in range(iters):
                mid = 0.5 * (a + b)
                if self.section_v(x, mid)[1] < z_arch:
                    a = mid
                else:
                    b = mid
            return 0.5 * (a + b)
        return None

    # --------------------------------------------------------- upper lines
    def upper_length(self, x):
        """Arc length of the section above the shoulder crease, metres."""
        pts = self.section(x)
        k = self._split_cache.get((round(x, 4), self.n_lower, self.n_upper), self.n_lower)
        return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                   for i in range(k, len(pts) - 1)) or 1.0

    def v_rail(self, x):
        """Section parameter of the roof rail / fender crown at station x.

        Window and rail lines are set as real distances from this edge rather
        than as fixed parameter values: the same v lands at very different
        distances below the rail along the car.
        """
        key = round(x, 4)
        hit = self._rail_cache.get(key)
        if hit is not None:
            return hit
        y_r = self.Y_ROOF(x)
        z_r = self.Z_ROOF(x) + self.Z_CREST(x)
        pts = self.section(x)
        n = len(pts)
        # Closest point on the polyline, not the closest vertex: snapping to a
        # vertex made v_rail a staircase along x and sawtoothed every edge.
        best = (1e9, 0.0)
        for j in range(n - 1):
            (y0, z0), (y1, z1) = pts[j], pts[j + 1]
            dy, dz = y1 - y0, z1 - z0
            L2 = dy * dy + dz * dz
            tt = 0.0 if L2 < 1e-14 else max(0.0, min(1.0, ((y_r - y0) * dy + (z_r - z0) * dz) / L2))
            d = (y0 + dy * tt - y_r) ** 2 + (z0 + dz * tt - z_r) ** 2
            if d < best[0]:
                best = (d, j + tt)
        i = best[1]
        k = self._split_cache.get((round(x, 4), self.n_lower, self.n_upper), self.n_lower)
        if i <= k:
            v = (i / float(k)) * self.V_SHOULDER
        else:
            v = self.V_SHOULDER + (i - k) / float(n - 1 - k) * (1.0 - self.V_SHOULDER)
        if len(self._rail_cache) > 20000:
            self._rail_cache.clear()
        self._rail_cache[key] = v
        return v

    def v_along(self, x, v, d):
        """v moved d metres along the upper section (+ toward the roof centre)."""
        return v + d / self.upper_length(x) * (1.0 - self.V_SHOULDER)

    def v_at_y_upper(self, x, y, iters=30):
        """Section parameter on the UPPER surface whose lateral offset is y."""
        a, b = self.V_SHOULDER, 1.0
        if self.section_v(x, a)[0] < y:
            return a
        if self.section_v(x, b)[0] > y:
            return b
        for _ in range(iters):
            mid = 0.5 * (a + b)
            if self.section_v(x, mid)[0] > y:
                a = mid
            else:
                b = mid
        return 0.5 * (a + b)

    def v_at_z(self, x, z, lo=0.0, hi=1.0, iters=30):
        """Section parameter whose height is z at station x (monotone region)."""
        a, b = lo, hi
        if self.section_v(x, lo)[1] > z:
            return lo
        if self.section_v(x, hi)[1] < z:
            return hi
        for _ in range(iters):
            mid = 0.5 * (a + b)
            if self.section_v(x, mid)[1] < z:
                a = mid
            else:
                b = mid
        return 0.5 * (a + b)

    def nearest_on_section(self, x, y, z):
        """Closest point on the half section at station x to (y, z): (y', z', v)."""
        pts = self.section(x)
        n = len(pts)
        best = (1e9, 0, 0.0, pts[0])
        for i in range(n - 1):
            (y0, z0), (y1, z1) = pts[i], pts[i + 1]
            dy, dz = y1 - y0, z1 - z0
            L2 = dy * dy + dz * dz
            t = 0.0 if L2 < 1e-14 else max(0.0, min(1.0, ((y - y0) * dy + (z - z0) * dz) / L2))
            qy, qz = y0 + dy * t, z0 + dz * t
            d = (qy - y) ** 2 + (qz - z) ** 2
            if d < best[0]:
                best = (d, i, t, (qy, qz))
        _, i, t, (qy, qz) = best
        f = i + t
        k_sh = self._split_cache.get((round(x, 4), self.n_lower, self.n_upper), self.n_lower)
        if f <= k_sh:
            v = (f / float(k_sh)) * self.V_SHOULDER
        else:
            v = self.V_SHOULDER + (f - k_sh) / float(n - 1 - k_sh) * (1.0 - self.V_SHOULDER)
        return (qy, qz, max(0.0, min(1.0, v)))

    # ------------------------------------------------------------- normals
    def surface_normal(self, x, v, eps=0.004):
        """Outward unit normal of the half surface at (x, v)."""
        x0, y0, z0 = self.surface(x, v)
        _, y1, z1 = self.surface(x, min(1.0, v + eps))
        _, y2, z2 = self.surface(min(self.HALF_L, x + eps), v)
        tv = (0.0, y1 - y0, z1 - z0)
        tx = (eps, y2 - y0, z2 - z0)
        nx = tv[1] * tx[2] - tv[2] * tx[1]
        ny = tv[2] * tx[0] - tv[0] * tx[2]
        nz = tv[0] * tx[1] - tv[1] * tx[0]
        L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        nx, ny, nz = nx / L, ny / L, nz / L
        # Point away from the body's core. Testing ny alone is a coin toss on
        # the top centreline, where the outward normal has ny ~ 0: it flipped
        # the SU7 hood's normal downward and hid the stripes inside the hood.
        if ny * y0 + nz * (z0 - self.core_z) < 0.0:
            nx, ny, nz = -nx, -ny, -nz
        return (nx, ny, nz)

    def surface_offset(self, x, v, d):
        """A point d metres proud of the body surface at (x, v)."""
        px, py, pz = self.surface(x, v)
        nx, ny, nz = self.surface_normal(x, v)
        return (px + nx * d, py + ny * d, pz + nz * d)

    # --------------------------------------------------------------- report
    def dims_report(self):
        xs = [-self.HALF_L + self.LENGTH * i / 200.0 for i in range(201)]
        max_y = max(max(p[0] for p in self.section(x)) for x in xs)
        max_z = max(self.Z_ROOF(x) for x in xs)
        min_z = min(self.Z_FLOOR(x) for x in xs)
        return {
            "length": self.LENGTH,
            "width": 2 * max_y,
            "height": max_z,
            "floor_min": min_z,
            "wheelbase": self.FRONT_AXLE - self.REAR_AXLE,
        }
