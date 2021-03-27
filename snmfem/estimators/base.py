import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted
from snmfem.updates import initialize_algorithms
from snmfem.laplacian import sigmaL, create_laplacian_matrix
from snmfem.measures import KLdiv_loss, KLdiv, Frobenius_loss
from snmfem.conf import log_shift
import time
from abc import ABC, abstractmethod 



class NMFEstimator(ABC, TransformerMixin, BaseEstimator):
    
    loss_names_ = ["KL divergence"]
    
    def __init__(self, n_components=None, init='warn', tol=1e-4, max_iter=200,
                 random_state=None, verbose=1, log_shift=log_shift, debug=False,
                 force_simplex=True, skip_G=False, l2=False,
                 ):
        self.n_components = n_components
        self.init = init
        self.tol = tol
        self.max_iter = max_iter
        self.random_state = random_state
        self.verbose = verbose
        self.log_shift = log_shift
        self.debug = debug
        self.force_simplex= force_simplex
        self.skip_G = skip_G
        self.const_KL_ = None
        self.l2 = l2

    def _more_tags(self):
        return {'requires_positive_X': True}

    @abstractmethod
    def _iteration(self,  P, A):
        pass

    def loss(self, P, A):
        GP = self.G_ @ P

        if self.l2:
            loss = Frobenius_loss(self.X_, GP, A, average=True) 
        else:
            if self.const_KL_ is None:
                self.const_KL_ = np.mean(self.X_*np.log(self.X_+ self.log_shift)) - np.mean(self.X_) 

            loss = KLdiv_loss(self.X_, GP, A, self.log_shift, safe=self.debug, average=True) + self.const_KL_
        self.detailed_loss_ = [loss]
        return loss

    def fit_transform(self, X, y=None, G=None, P=None, A=None, shape_2d = None, eval_print=10):
        """Learn a NMF model for the data X and returns the transformed data.
        This is more efficient than calling fit followed by transform.
        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Data matrix to be decomposed
        P : array-like of shape (n_samples, n_components)
            If specified, it is used as initial guess for the solution.
        A : array-like of shape (n_components, n_features)
            If specified, it is used as initial guess for the solution.
        Returns
        -------
        P, A : ndarrays
        """
        self.X_ = self._validate_data(X, dtype=[np.float64, np.float32])
        self.const_KL_ = None
        
        if self.skip_G:
            G = None
        self.G_, self.P_, self.A_ = initialize_algorithms(self.X_, G, P, A, self.n_components, self.init, self.random_state, self.force_simplex)
        
        self.shape_2d_ = shape_2d
        if not(self.shape_2d_ is None) :
            self.L_ = create_laplacian_matrix(*self.shape_2d_)

        algo_start = time.time()
        # If mu_sparse != 0, this is the regularized step of the algorithm
        # Otherwise this is directly the data fitting step
        eval_before = np.inf
        self.n_iter_ = 0

        # if self.debug:
        self.losses_ = []
        self.rel_ = []
        self.detailed_losses_ = []

        try:
            while True:
                # Take one step in A, P
                old_P, old_A = self.P_.copy(), self.A_.copy()
                self.P_, self.A_ = self._iteration( self.P_, self.A_ )
                eval_after = self.loss(self.P_, self.A_)
                self.n_iter_ +=1
                
                rel_P = np.max((self.P_ - old_P)/(self.P_ + self.tol*np.mean(self.P_) ))
                rel_A = np.max((self.A_ - old_A)/(self.A_ + self.tol*np.mean(self.A_) ))


                # store some information for assessing the convergence
                # for debugging purposes
                # if self.debug:
                self.losses_.append(eval_after)
                self.detailed_losses_.append(self.detailed_loss_)
                self.rel_.append([rel_P,rel_A])

                # check convergence criterions
                if self.n_iter_ >= self.max_iter:
                    print("exits because max_iteration was reached")
                    break

                # If there is no regularization the algorithm stops with this criterion
                # Otherwise it goes to the data fitting step
                elif max(rel_A,rel_P) < self.tol:
                    print(
                        "exits because of relative change rel_A {} or rel_P {} < tol ".format(
                            rel_A,rel_P
                        )
                    )
                    break
                elif abs((eval_before - eval_after)/min(eval_before, eval_after)) < self.tol:
                    print(
                        "exits because of relative change < tol: {}".format(
                            (eval_before - eval_after)/min(eval_before, eval_after)
                        )
                    )
                    break

                elif np.isnan(eval_after):
                    print("exit because of the presence of NaN")
                    break

                elif (eval_before - eval_after) < 0:
                    print("exit because of negative decrease")
                    break
                
                if self.verbose > 0 and np.mod(self.n_iter_, eval_print) == 0:
                    print(
                        f"It {self.n_iter_} / {self.max_iter}: loss {eval_after:0.3f},  {self.n_iter_/(time.time()-algo_start):0.3f} it/s",
                    )
                eval_before = eval_after
        except KeyboardInterrupt:
            pass

        algo_time = time.time() - algo_start
        print(
            f"Stopped after {self.n_iter_} iterations in {algo_time//60} minutes "
            f"and {np.round(algo_time) % 60} seconds."
        )

        self.reconstruction_err_ = self.loss(self.P_, self.A_)

        self.n_components_ = self.A_.shape[0]
        self.components_ = self.A_

        GP = self.G_ @ self.P_

        return GP

    def fit(self, X, y=None, **params):
        """Learn a NMF model for the data X.
        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Data matrix to be decomposed
        y : Ignored
        Returns
        -------
        self
        """
        self.fit_transform(X, **params)
        return self

    # def transform(self, X):
    #     """Transform the data X according to the fitted NMF model.
    #     Parameters
    #     ----------
    #     X : {array-like, sparse matrix} of shape (n_samples, n_features)
    #         Data matrix to be transformed by the model.
    #     Returns
    #     -------
    #     P : ndarray of shape (n_samples, n_components)
    #         Transformed data.
    #     """
    #     check_is_fitted(self)
    #     X = self._validate_data(X, accept_sparse=('csr', 'csc'),
    #                             dtype=[np.float64, np.float32],
    #                             reset=False)

    #     return self.P_

    def inverse_transform(self, P):
        """Transform data back to its original space.
        Parameters
        ----------
        P : {ndarray, sparse matrix} of shape (n_samples, n_components)
            Transformed data matrix.
        Returns
        -------
        X : {ndarray, sparse matrix} of shape (n_samples, n_features)
            Data matrix of original shape.
        .. versionadded:: 0.18
        """
        check_is_fitted(self)
        return self.G_ @ P @ self.A_
    
    def get_losses(self):
        names = ["full_loss"] + self.loss_names_ + ["rel_P","rel_A"]

        dt_list = []
        for elt in names : 
            dt_list.append((elt,"float64"))
        dt = np.dtype(dt_list)

        tup_list = []
        for i in range(len(self.losses_)) : 
            tup_list.append((self.losses_[i],) + tuple(self.detailed_losses_[i]) + tuple(self.rel_[i]))
        
        array = np.array(tup_list,dtype=dt)

        return array