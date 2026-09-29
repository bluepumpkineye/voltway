"""CarBody: the flank loft and the two end caps, seen as one surface.

This is what parts are placed on. `project` finds the nearest point on
whichever surface is nearer (nose cap, tail cap or flank) with its normal;
`side_point` evaluates the smooth surface at a side-elevation position (x, z)
on the left flank, round into the caps at either end.
"""


class CarBody:
    def __init__(self, loft, nose, tail, flank_x_range=None):
        self.loft = loft
        self.nose = nose
        self.tail = tail
        # stations where the flank is a candidate for projection
        self.flank_x_range = flank_x_range or (-loft.HALF_L + 0.10, loft.HALF_L - 0.15)

    def cap(self, front):
        return self.nose if front else self.tail

    # ------------------------------------------------------------ projection
    def project(self, p):
        """Nearest point on the body - nose cap, tail cap or flank - and its
        normal. Works on the +Y half; everything is built there and mirrored."""
        x, y, z = p
        front = x > 0.0
        cap = self.nose if front else self.tail
        S = self.loft
        cands = []
        w, v = cap.wv_at(max(0.0, y), z)
        q = cap.point(w, v)
        cands.append(((q[0] - x) ** 2 + (q[1] - y) ** 2 + (q[2] - z) ** 2,
                      q, cap.normal(w, v)))
        lo, hi = self.flank_x_range
        if lo < x < hi:
            qy, qz, vf = S.nearest_on_section(x, y, z)
            if self.tail.JOIN(vf) - 1e-4 <= x <= self.nose.JOIN(vf) + 1e-4:
                q = (x, qy, qz)
                cands.append(((qy - y) ** 2 + (qz - z) ** 2, q,
                              S.surface_normal(x, vf)))
        cands.sort(key=lambda c: c[0])
        return cands[0][1], cands[0][2]

    def proud(self, p, d):
        """project(p), pushed d metres along the normal."""
        q, n = self.project(p)
        return (q[0] + n[0] * d, q[1] + n[1] * d, q[2] + n[2] * d), n

    def side_point(self, x, z):
        """The body's outer surface at side-elevation position (x, z) on the
        left side, with its outward normal - from the analytic surfaces.

        Prefer this to ray casts for anything broad that spans the flank and a
        cap: rays hit panels, recesses and gaps in turn and the part crumples.
        """
        S = self.loft
        v = S.v_at_z(x, z, 0.0, S.V_SHOULDER)
        if x >= 0.0:
            cap = self.nose
            on_flank = x <= cap.JOIN(v)
        else:
            cap = self.tail
            on_flank = x >= cap.JOIN(v)
        if on_flank:
            y = S.section_v(x, v)[0]
            return (x, y, z), S.surface_normal(x, v)
        w, v = cap.wv_at_xz(x, z)
        return cap.point(w, v), cap.normal(w, v)

    # ---------------------------------------------------------------- report
    def dims_report(self, n=48):
        pts_f = [self.nose.point(w / n, v / n) for w in range(n + 1) for v in range(n + 1)]
        pts_r = [self.tail.point(w / n, v / n) for w in range(n + 1) for v in range(n + 1)]
        return dict(front_max=max(p[0] for p in pts_f),
                    rear_min=min(p[0] for p in pts_r),
                    front_half_w=max(p[1] for p in pts_f),
                    length=max(p[0] for p in pts_f) - min(p[0] for p in pts_r))
