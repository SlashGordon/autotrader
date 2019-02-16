# -*- coding: utf-8 -*-
""" Autotrader

 Copyright 2017-2018 Slash Gordon

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
import numpy as np


class StringCompareHelper:
    """
    Little helper class for string comparision
    """
    @staticmethod
    def levenshtein_ratio_and_distance(s, t):
        """ levenshtein_ratio_and_distance:
            Calculates levenshtein distance between two strings.
            If ratio_calc = True, the function computes the
            levenshtein distance ratio of similarity between two strings
            For all i and j, distance[i,j] will contain the Levenshtein
            distance between the first i characters of s and the
            first j characters of t
        """
        # Initialize matrix of zeros
        rows = len(s)+1
        cols = len(t)+1
        distance = np.zeros((rows, cols), dtype=int)

        # Populate matrix of zeros with the indeces of each character of both strings
        for i in range(1, rows):
            for k in range(1, cols):
                distance[i][0] = i
                distance[0][k] = k

        # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
        for col in range(1, cols):
            for row in range(1, rows):
                if s[row-1] == t[col-1]:
                    cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
                else:
                    cost = 2
                distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                     distance[row][col-1] + 1,          # Cost of insertions
                                     distance[row-1][col-1] + cost)     # Cost of substitutions
        # Computation of the Levenshtein Distance Ratio
        Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return Ratio
