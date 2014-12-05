##
# SurrogateBenchmarks: A program making it easy to benchmark hyperparameter
# optimization software .
# Copyright (C) 2014 Katharina Eggensperger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = ["Katharina Eggensperger"]

from Surrogates.RegressionModels import ScikitBaseClass

import sys
import time

import numpy
numpy.random.seed(1)

from scipy.stats import uniform

from sklearn.cross_validation import train_test_split
from sklearn.grid_search import ParameterSampler
from sklearn.linear_model import Lasso

from Surrogates.DataExtraction.data_util import read_csv


class LassoRegression(ScikitBaseClass.ScikitBaseClass):

    def __init__(self, sp, encode, rng=1, **kwargs):
        ScikitBaseClass.ScikitBaseClass.__init__(self, sp=sp, encode=encode, rng=rng, **kwargs)
        self._name = "RidgeRegression " + str(encode)

    def _random_search(self, random_iter, x, y):
        # Default Values
        alpha = 1.0
        best_score = -sys.maxint

        if random_iter > 0:
            sys.stdout.write("Do a random search %d times" % random_iter)
            param_dist = {"alpha": uniform(loc=0.0001, scale=10-0.0001)}
            param_list = [{"alpha": alpha}, ]
            param_list.extend(list(ParameterSampler(param_dist, n_iter=random_iter-1, random_state=self._rng)))
            for idx, d in enumerate(param_list):
                lasso = Lasso(alpha=d["alpha"],
                              fit_intercept=True,
                              normalize=False,
                              precompute='auto',
                              copy_X=True,
                              max_iter=1000,
                              tol=0.0001,
                              warm_start=False,
                              positive=False)

                train_x, test_x, train_y, test_y = train_test_split(x, y, test_size=0.5, random_state=self._rng)
                lasso.fit(train_x, train_y)
                sc = lasso.score(test_x, test_y)
                # Tiny output
                m = "."
                if idx % 10 == 0:
                    m = "#"
                if sc > best_score:
                    m = "<"
                    best_score = sc
                    alpha = d['alpha']
                sys.stdout.write(m)
                sys.stdout.flush()
            sys.stdout.write("Using alpha: %f\n" % alpha)
        return alpha

    def train(self, x, y, param_names, random_search=100, **kwargs):
        start = time.time()
        scaled_x = self._set_and_preprocess(x=x, param_names=param_names)

        # Check that each input is between 0 and 1
        self._check_scaling(scaled_x=scaled_x)

        if self._debug:
            print "Shape of training data: ", scaled_x.shape
            print "Param names: ", self._used_param_names
            print "First training sample\n", scaled_x[0]
            print "Encode: ", self._encode

        # Do a random search
        alpha = self._random_search(random_iter=100, x=scaled_x, y=y)

        # Now train model
        lasso = Lasso(alpha=alpha,
                      fit_intercept=True,
                      normalize=False,
                      precompute='auto',
                      copy_X=True,
                      max_iter=1000,
                      tol=0.0001,
                      warm_start=False,
                      positive=False)

        lasso.fit(scaled_x, y)
        self._model = lasso

        duration = time.time() - start
        self._training_finished = True
        return duration


def test():
    from sklearn.metrics import mean_squared_error
    import Surrogates.DataExtraction.pcs_parser as pcs_parser
    sp = pcs_parser.read(file("/home/eggenspk/Surrogates/Data_extraction/Experiments2014/hpnnet/smac_2_06_01-dev/nips2011.pcs"))
    # Read data from csv
    header, data = read_csv("/home/eggenspk/Surrogates/Data_extraction/hpnnet_nocv_convex_all/hpnnet_nocv_convex_all_fastrf_results.csv",
                            has_header=True, num_header_rows=3)
    para_header = header[0]
    type_header = header[1]
    cond_header = header[2]
    checkpoint = hash(numpy.array_repr(data))
    assert checkpoint == 246450380584980815

    model = LassoRegression(sp=sp, encode=False, debug=True)
    x_train_data = data[:1000, :-2]
    y_train_data = data[:1000, -1]
    x_test_data = data[1000:, :-2]
    y_test_data = data[1000:, -1]

    model.train(x=x_train_data, y=y_train_data, param_names=para_header, rng=1)

    y = model.predict(x=x_train_data[1, :])
    print "Is: %100.70f, Should: %f" % (y, y_train_data[1])
    assert y[0] == 0.321388102019576071821660434579825960099697113037109375

    print "Predict whole data"
    y_whole = model.predict(x=x_test_data)
    mse = mean_squared_error(y_true=y_test_data, y_pred=y_whole)
    print "MSE: %100.70f" % mse
    assert mse == 0.00851109857254793433778417011126293800771236419677734375

    print "Soweit so gut"

    # Try the same with encoded features
    model = LassoRegression(sp=sp, encode=True, debug=True)
    #print data[:10, :-2]
    model.train(x=x_train_data, y=y_train_data, param_names=para_header, rng=1)

    y = model.predict(x=x_train_data[1, :])
    print "Is: %100.70f, Should: %f" % (y, y_train_data[1])
    assert y[0] == 0.318432843840318391404053954829578287899494171142578125

    print "Predict whole data"
    y_whole = model.predict(x=x_test_data)
    mse = mean_squared_error(y_true=y_test_data, y_pred=y_whole)
    print "MSE: %100.70f" % mse
    assert mse == 0.00836139846303437204999564613672191626392304897308349609375

    assert hash(numpy.array_repr(data)) == checkpoint


if __name__ == "__main__":
    outer_start = time.time()
    test()
    dur = time.time() - outer_start
    print "TESTING TOOK: %f sec" % dur