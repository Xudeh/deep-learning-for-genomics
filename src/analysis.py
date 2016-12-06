#!/usr/bin/env python

import data

from matplotlib import pyplot
import seaborn

from numpy import linspace, random, nonzero, where, inf, log, exp, empty, arange
from sklearn.decomposition import PCA

from aux import labelWithDefaultSymbol

palette = seaborn.color_palette('Set2', 8)
seaborn.set(style='ticks', palette = palette)

pyplot.rcParams.update({'figure.max_open_warning': 0})

def analyseData(data_set, name = "data", intensive_calculations = False):
    
    N, D = data_set.shape
    
    if intensive_calculations:
        plotHeatMap(data_set, name)
    
    average_cell = data_set.mean(axis = 0)
    average_cell_name = name + "/mean"
    plotProfile(average_cell, average_cell_name)
    
    subset = random.randint(N, size = 10)
    for j, i in enumerate(subset):
        cell = data_set[i]
        cell_name = name + "/cell_{}".format(j)
        plotProfile(cell, cell_name)
    
    # average_genes_per_cell = data_set.sum(axis = 1)
    # print(average_genes_per_cell.std() / average_genes_per_cell.mean())

def analyseModel(model, name = "model"):
    
    plotLearningCurves(model.learning_curves, name)

def analyseResults(x_test, x_test_recon, x_test_headers, clusters, latent_set,
    x_sample, name = "results", intensive_calculations = False):
    
    N, D = x_test.shape
    
    data_sets = [
        {"data_set": x_test, "name": "Test", "tolerance": 0.5},
        {"data_set": x_test_recon["mean"], "name": "Reconstructed",
         "tolerance": 0.5},
    ]
    
    for variable_name in x_test_recon:
        
        if variable_name == "mean":
            continue
        
        if "log" in variable_name:
            variable = exp(x_test_recon[variable_name])
        else:
            variable = x_test_recon[variable_name]
        
        variable_name = variable_name.replace("log_", "")
        
        data_set = {"data_set": variable, "name": variable_name}
        data_sets.append(data_set)
    
    printSummaryStatistics([statistics(**data_set) for data_set in data_sets])
    
    print("")
    
    if intensive_calculations:
        print("Creating heat maps.")
        
        test_set_name = name + "/test"
        plotHeatMap(x_test, x_test_headers, clusters, name = test_set_name)
        
        reconstructed_test_set_name = name + "/test_recon"
        plotHeatMap(x_test_recon["mean"], x_test_headers, clusters,
            name = reconstructed_test_set_name)
        
        difference_name = name + "/test_difference"
        plotHeatMap(x_test - x_test_recon["mean"], x_test_headers, clusters,
            name = difference_name)
        
        log_ratio_name = name + "/test_log_ratio"
        plotHeatMap(log(x_test / x_test_recon["mean"] + 1), x_test_headers, clusters,
            name = log_ratio_name)
    
    print("Creating latent space scatter plot.")
    plotLatentSpace(latent_set, x_test_headers, clusters, name)
    
    subset = random.randint(N, size = 10)
    for j, i in enumerate(subset):
        
        print("Creating profiles for cell {}.".format(x_test_headers["cells"][i]))
        
        label = labelWithDefaultSymbol("x")
        
        cell_test = x_test[i]
        cell_test_name = name + "/cell_{}_test".format(j)
        plotProfile(cell_test, label(), cell_test_name)
        
        for variable_name in x_test_recon:
            
            cell_recon = x_test_recon[variable_name][i]
            cell_recon_name = name + "/cell_{}_recon_{}".format(j, variable_name)
            plotProfile(cell_recon, label(variable_name), cell_recon_name)
            
            if variable_name == "mean":
                cell_diff = cell_test - cell_recon
                cell_diff_name = name + "/cell_{}_diff".format(j)
                plotProfile(cell_diff, label() + "$-$" + label(variable_name), cell_diff_name)
        

def statistics(data_set, name = "", tolerance = 1e-3):
    
    statistics = {
        "name": name,
        "mean": data_set.mean(),
        "std": data_set.std(),
        "min": data_set.min(),
        "minimums": (data_set < data_set.min() + tolerance).sum(),
        "max": data_set.max(),
        "maximums": (data_set >= data_set.max() - tolerance).sum(),
        "sparsity": float((data_set < tolerance).sum()) / float(data_set.size)
    }
    
    return statistics

def printSummaryStatistics(statistics_sets):
    
    if type(statistics_sets) != list:
        statistics_sets = [statistics_sets]
    
    name_width = 0
    
    for statistics_set in statistics_sets:
        name_width = max(len(statistics_set["name"]), name_width)
    
    print("Statistics:")
    print("  ".join(["{:{}}".format("Data set", name_width), "mean", "std ", " minimum ", "n_minimum", " maximum ", "n_maximum", "sparsity"]))
    
    for statistics_set in statistics_sets:
        string_parts = [
            "{:{}}".format(statistics_set["name"], name_width),
            "{:<4.2f}".format(statistics_set["mean"]),
            "{:<4.2g}".format(statistics_set["std"]),
            "{:<9.3g}".format(statistics_set["min"]),
            "{:>7d}".format(statistics_set["minimums"]),
            "{:<9.3g}".format(statistics_set["max"]),
            "{:>7d}".format(statistics_set["maximums"]),
            "{:<7.5g}".format(statistics_set["sparsity"]),
        ]
        
        print("  ".join(string_parts))

def plotProfile(cell, label, name = None):
    
    figure_name = "profile"
    
    if name:
        figure_name = name + "_" + figure_name
    
    D = cell.shape[0]
    
    figure = pyplot.figure()
    axis = figure.add_subplot(1, 1, 1)
    
    x = linspace(0, D, D)
    # axis.bar(x, cell)
    axis.plot(x, cell)
    
    axis.set_xlabel("Cell")
    axis.set_ylabel(label)
    
    data.saveFigure(figure, figure_name)

def plotHeatMap(data_set, data_set_headers = None, clusters = None, name = None):
    
    figure_name = "heat_map"
    
    if name:
        figure_name = name + "_" + figure_name
    
    if data_set_headers and clusters:
    
        sorted_data_set = empty(data_set.shape)
    
        N_seen = 0
        for cluster_id, cluster in sorted(clusters.items()):
            
            subset = []
            
            for cell in cluster:
                index = where(data_set_headers["cells"] == cell)[0]
                if len(index) == 0:
                    continue
                subset.append(int(index))
            
            N_subset = len(subset)
            
            if N_subset == 0:
                continue
            
            sorted_data_set[N_seen:(N_seen + N_subset)] = data_set[subset]
        
            N_seen += N_subset
        
        data_set = sorted_data_set[:N_seen]
        figure_name += "_sorted"
    
    N, M = data_set.shape
    
    # figure = pyplot.figure(figsize = (N/500, M/500))
    figure = pyplot.figure()
    axis = figure.add_subplot(1, 1, 1)
    
    seaborn.heatmap(data_set.T, xticklabels = False, yticklabels = False, cbar = True,
        square = True, ax = axis)
    
    axis.set_xlabel("Cell")
    axis.set_ylabel("Gene")
    
    data.saveFigure(figure, figure_name, no_spine = False)

def plotLearningCurves(curves, name = None):
    
    figure_1_name = "learning_curves"
    figure_2_name = "learning_curves_KL"
    
    if name:
        figure_1_name = name + "/" + figure_1_name
        figure_2_name = name + "/" + figure_2_name
    
    figure_1 = pyplot.figure()
    axis_1 = figure_1.add_subplot(1, 1, 1)
    
    figure_2 = pyplot.figure()
    axis_2 = figure_2.add_subplot(1, 1, 1)
    
    for i, (curve_set_name, curve_set) in enumerate(sorted(curves.items())):
        
        colour = palette[i]
        
        for curve_name, curve in sorted(curve_set.items()):
            if curve_name == "lower bound":
                line_style = "solid"
                curve_name = curve_name.capitalize()
                axis = axis_1
            elif curve_name == "log p(x|z)":
                line_style = "dashed"
                axis = axis_1
            elif curve_name == "KL divergence":
                line_style = "dashed"
                axis = axis_2
            epochs = arange(len(curve)) + 1
            label = curve_name + " ({} set)".format(curve_set_name)
            axis.plot(curve, color = colour, linestyle = line_style, label = label)
    
    axis_1.legend(loc = "best")
    axis_2.legend(loc = "best")
    
    axis_1.set_xlabel("Epoch")
    axis_2.set_xlabel("Epoch")
    
    # axis_1.set_ylabel("Learning curve")
    # axis_2.set_ylabel("KL divergence")
    
    data.saveFigure(figure_1, figure_1_name)
    data.saveFigure(figure_2, figure_2_name)

def plotLatentSpace(latent_set, latent_set_headers = None, clusters = None, name = None):
    
    figure_name = "latent_space"
    
    if name:
        figure_name = name + "/" + figure_name
    
    N, M = latent_set.shape
    
    figure = pyplot.figure()
    axis = figure.add_subplot(1, 1, 1)
    
    if M > 2:
        pca = PCA(n_components = 2)
        pca.fit(latent_set)
        latent_set = pca.transform(latent_set)
        
        axis.set_xlabel("PC 1")
        axis.set_ylabel("PC 2")
    else:
        axis.set_xlabel("z_1")
        axis.set_ylabel("z_2")
    
    for cluster_id in clusters:
        
        cluster = clusters[cluster_id]
        subset = []
    
        for cell in cluster:
            index = where(latent_set_headers["cells"] == cell)[0]
            # print(index) # cells in headers, and hence in test set, are clustered
            if len(index) == 0:
                continue
            subset.append(int(index))
        
        if len(subset) == 0:
            continue
        
        axis.scatter(latent_set[subset, 0], latent_set[subset, 1],
            c = data.cluster_colours[cluster_id], edgecolors = None,
            label = cluster_id)
    
    axis.legend(loc="best")
    
    data.saveFigure(figure, figure_name)

if __name__ == '__main__':
    random.seed(1234)
    data_set = data.createSampleData(1000, 500, p = 0.95)
    analyseData(data_set, name = "sample", intensive_calculations = True)
