##############################################################################
# Copyright (c) 2013-2016, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Created by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://github.com/llnl/spack
# Please also see the LICENSE file for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (as
# published by the Free Software Foundation) version 2.1, February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
from spack import *
import sys


class Nwchem(Package):
    """High-performance computational chemistry software"""

    homepage = "http://www.nwchem-sw.org"
    url      = "http://www.nwchem-sw.org/images/Nwchem-6.6.revision27746-src.2015-10-20.tar.gz"

    version('6.6', 'c581001c004ea5e5dfacb783385825e3',
            url='http://www.nwchem-sw.org/images/Nwchem-6.6.revision27746-src.2015-10-20.tar.gz')

    depends_on('blas')
    depends_on('lapack')
    depends_on('mpi')
    depends_on('scalapack')

    depends_on('python@2.7:2.8', type='build')

    def install(self, spec, prefix):
        # see http://www.nwchem-sw.org/index.php/Compiling_NWChem
        args = []
        args.extend([
            'NWCHEM_TOP=%s' % self.stage.source_path,
            'USE_MPI=y',
            'MPI_LOC=%s' % spec['mpi'].prefix,
            'USE_PYTHONCONFIG=y',
            'PYTHONVERSION=%s' % spec['python'].version.up_to(2),
            'BLASOPT=%s %s' % (
                to_link_flags(spec['lapack'].lapack_shared_lib),
                to_link_flags(spec['blas'].blas_shared_lib)),
            'USE_SCALAPACK=y',
            'SCALAPACK=%s' % spec['scalapack'].fc_link,
            'NWCHEM_MODULES=all',
            'NWCHEM_LONG_PATHS=Y'  # by default NWCHEM_TOP is 64 char max
        ])

        # TODO: query if blas/lapack/scalapack uses 64bit Ints
        # A flag to distinguish between 32bit and 64bit integers in linear
        # algebra (Blas, Lapack, Scalapack)
        use32bitLinAlg = True

        if use32bitLinAlg:
            args.extend([
                'USE_64TO32=y',
                'BLAS_SIZE=4',
                'SCALAPACK_SIZE=4'
            ])
        else:
            args.extend([
                'BLAS_SIZE=8',
                'SCALAPACK_SIZE=8'
            ])

        if sys.platform == 'darwin':
            target = 'MACX64'
            args.extend([
                'CFLAGS_FORGA=-DMPICH_NO_ATTR_TYPE_TAGS'
            ])
        else:
            target = 'LINUX64'

        args.extend(['NWCHEM_TARGET=%s' % target])

        with working_dir('src'):
            make('nwchem_config', *args)
            if use32bitLinAlg:
                make('64_to_32', *args)
            make(*args)

            #  need to install by hand. Follow Ubuntu:
            #  http://packages.ubuntu.com/trusty/all/nwchem-data/filelist
            #  http://packages.ubuntu.com/trusty/amd64/nwchem/filelist
            share_path = join_path(prefix, 'share', 'nwchem')
            mkdirp(prefix.bin)

            install_tree('data', share_path)
            install_tree(join_path('basis', 'libraries'),
                         join_path(share_path, 'libraries'))
            install_tree(join_path('nwpw', 'libraryps'),
                         join_path(share_path, 'libraryps'))

            b_path = join_path(self.stage.source_path, 'bin',
                               target, 'nwchem')
            chmod = which('chmod')
            chmod('+x', b_path)
            install(b_path, prefix.bin)

            # Finally, make user's life easier by creating a .nwchemrc file
            # to point to the required data files.
            nwchemrc = """\
   nwchem_basis_library {data}/libraries/
   nwchem_nwpw_library {data}/libraryps/
   ffield amber
   amber_1 {data}/amber_s/
   amber_2 {data}/amber_q/
   amber_3 {data}/amber_x/
   amber_4 {data}/amber_u/
   spce    {data}/solvents/spce.rst
   charmm_s {data}/charmm_s/
   charmm_x {data}/charmm_x/
""".format(data=share_path)
            with open(".nwchemrc", 'w') as f:
                f.write(nwchemrc)
            install(".nwchemrc", share_path)
