import pandas as pd
import numpy as np
from scipy import stats
import json
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.backends.backend_agg as agg
matplotlib.use('Agg')
import pprint
import base64
from io import BytesIO
from scipy.stats import chi2_contingency
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from statsmodels.tools.sm_exceptions import PerfectSeparationError
from numpy.linalg import LinAlgError

def load_dataframe(FILE_PATH):
    '''
    loads data from CSV, Excel, JSON, or Feather files into a pandas DataFrame.
    INPUT: File Path
    OUTPUT: Loaded Pandas DF
    '''
    if FILE_PATH.endswith('.csv'):
        df = pd.read_csv(FILE_PATH, low_memory=False)
        print('CSV file found.')
    elif FILE_PATH.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(FILE_PATH)
        print('Excel file found.')
    elif FILE_PATH.endswith('.json'):
        df = pd.read_json(FILE_PATH)
        print('JSON file found.')
    elif FILE_PATH.endswith('.feather'):
        df = pd.read_feather(FILE_PATH)
        print('Feather file found.')
    else:
        raise ValueError(f"Unsupported File Format: {FILE_PATH}. Please provide a CSV, Excel, Json or Feather file format.")
    return df

def generate_outlier_plot(df, column):
    """Generate an enhanced outlier plot with better spacing and axis limits"""
    fig, ax = plt.subplots(figsize=(10, 5)) 
    data = df[column].replace([np.inf, -np.inf], np.nan).dropna()
    z_scores = np.abs(stats.zscore(data))
    n_points = len(data)
    mask_3_4 = (z_scores > 3) & (z_scores <= 4)
    mask_4_5 = (z_scores > 4) & (z_scores <= 5)
    mask_5_plus = z_scores > 5
    ax.scatter(np.where(z_scores <= 3)[0], data[z_scores <= 3], 
               c='#1f77b4', alpha=0.6, s=40, label='Normal (≤3σ)')
    ax.scatter(np.where(mask_3_4)[0], data[mask_3_4], 
               c='#ff7f0e', alpha=0.8, s=60, label='Outliers (3-4σ)')
    ax.scatter(np.where(mask_4_5)[0], data[mask_4_5], 
               c='#d62728', alpha=0.8, s=80, label='Outliers (4-5σ)')
    ax.scatter(np.where(mask_5_plus)[0], data[mask_5_plus], 
               c='#9467bd', alpha=0.9, marker='X', s=100, label='Extreme (>5σ)')
    ax.set_xlim(-0.02*n_points, n_points*1.02 - 1) 
    y_padding = 0.02 * (data.max() - data.min())
    ax.set_ylim(data.min() - y_padding, data.max() + y_padding)
    ax.set_title(f'Outliers in {column}', fontsize=14, pad=10)
    ax.set_xlabel('Data Point Index', fontsize=11)
    ax.set_ylabel(column, fontsize=11)
    legend = ax.legend(title="Outlier Categories", 
                      bbox_to_anchor=(1.02, 1), 
                      loc='upper left',
                      borderaxespad=0.3,  
                      framealpha=0.9)
    legend.get_title().set_fontsize('11')  
    fig.set_constrained_layout(True)
    fig.set_constrained_layout_pads(w_pad=0.3, h_pad=0.3)  
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def generate_skewness_plot(df, column):
    """Generate a distribution plot showing skewness"""
    fig, ax = plt.subplots(figsize=(10, 5))
    data = df[column].replace([np.inf, -np.inf], np.nan).dropna()
    mean = data.mean()
    median = data.median()
    skewness = data.skew()
    sns.histplot(data, kde=True, ax=ax, color='#1f77b4', alpha=0.6)
    ax.axvline(mean, color='#ff7f0e', linestyle='--', linewidth=2, label=f'Mean ({mean:.2f})')
    ax.axvline(median, color='#2ca02c', linestyle=':', linewidth=2, label=f'Median ({median:.2f})')
    ax.set_title(f'Distribution of {column}\nSkewness: {skewness:.2f}', fontsize=14, pad=15)
    ax.set_xlabel(column, fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.legend(loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def check_timeseries(df, col):
    '''
    Efficiently checks if a column contains datetime data and whether it forms a proper time series.
    INPUT: Dataframe, Column
    OUTPUT: Dictionary
    '''
    if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_bool_dtype(df[col]):
        return {'timeseries': False, 'datetime': False}
    date_formats = [
        '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d', '%d%m%Y', '%m%d%Y',
        '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S',
        '%Y%m%d%H%M%S', '%d%m%Y%H%M%S', '%m%d%Y%H%M%S', '%b %d %Y', '%d %b %Y', '%B %d %Y', '%d %B %Y',
        '%Y-%m-%dT%H:%M:%S', '%d-%m-%Y %I:%M:%S %p', '%m-%d-%Y %I:%M:%S %p',
        '%Y-%m-%d %I:%M:%S %p', '%d/%m/%Y %I:%M:%S %p'
    ]
    return_dict = {
        'timeseries': False,
        'datetime': False,
    }
    col_data = df[col]
    if pd.api.types.is_datetime64_any_dtype(col_data):
        return_dict['datetime'] = True
        min_val = col_data.min()
        max_val = col_data.max()
        return_dict['min'] = min_val
        return_dict['max'] = max_val
        if col_data.is_monotonic_increasing or col_data.is_monotonic_decreasing:
            return_dict['timeseries'] = True
            return_dict['days_span'] = (max_val - min_val).days
        return return_dict
    for fmt in date_formats:
        try:
            parsed = pd.to_datetime(col_data, format=fmt, errors='coerce')
            if parsed.notna().all():
                return_dict['datetime'] = True
                min_val = parsed.min()
                max_val = parsed.max()
                return_dict['min'] = min_val
                return_dict['max'] = max_val
                return_dict['format'] = fmt
                if parsed.is_monotonic_increasing or parsed.is_monotonic_decreasing:
                    return_dict['timeseries'] = True
                    return_dict['days_span'] = (max_val - min_val).days

                return return_dict 
        except Exception:
            continue 
    return return_dict

def data_quality_check(df):
    print("Performing data quality check...")
    '''
    Data type classification (numeric, boolean, datetime, timeseries, etc.)
    Basic statistics (mean, std, min, max for numeric columns)
    Outlier detection using z-scores (3σ, 4σ, 5σ thresholds)
    Skewness and kurtosis calculations
    Unique value analysis for categorical data
    INPUT: Dataframe
    OUTPUT: Dictionary: Top Level (Datatype, Counts, Columns), Lower Level (Column Summary Data)
    '''
    # Checking Data Types of Columns
    dtype_analysis = {}
    for col in df.columns:
        dtype = None
        timeseries_data = {'timeseries': False, 'datetime': False}
        col_sample = df[col].dropna().astype(str).head(10)
        if df[col].dtype == 'object' and col_sample.str.contains(r"\d{4}|\d{2}").any():
            timeseries_data = check_timeseries(df, col)
            if timeseries_data['timeseries']:
                dtype = 'timeseries'
            elif timeseries_data['datetime']:
                dtype = 'datetime'
        elif df[col].dropna().isin([0, 1, 0.0, 1.0, True, False]).all() or df[col].dtype == 'bool':
            dtype = 'boolean'
        if dtype is None:
            dtype = str(df[col].dtype)
        # Initialise dtype entry if the type is not yet initialised
        if dtype not in dtype_analysis:
            dtype_analysis[dtype] = {
                'count': 0,
                'columns': {}, # Nested Dictionary for Column Data
            }
        dtype_analysis[dtype]['count'] += 1

        sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
        unique_count = df[col].nunique()
        null_count = df[col].isnull().sum()

        # Store basic column level stats
        col_stats = {
            'null_count': null_count,
            'dtype': dtype,
        }

        if timeseries_data['datetime']:
            col_stats.update(timeseries_data)

        # Create and store numeric and outlier stats
        if np.issubdtype(df[col].dtype, np.number) and unique_count > 1 and dtype != 'boolean':
            col_stats['sample_value'] = sample_value
            col_stats['unique_count'] = unique_count
            col_stats['mean'] = df[col].mean()
            col_stats['std'] = df[col].std()
            col_stats['min'] = df[col].min()
            col_stats['max'] = df[col].max()
            col_stats['population_variance'] = df[col].var(ddof=0)
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            outliers_3sigma = (z_scores > 3).sum()
            outliers_4sigma = (z_scores > 4).sum()
            outliers_5sigma = (z_scores > 5).sum()
            col_stats['outliers'] = {
                '> 3σ': outliers_3sigma,
                '> 4σ': outliers_4sigma,
                '> 5σ': outliers_5sigma,
            }

            col_stats['skewness'] = df[col].skew()
            col_stats['kurtosis'] = df[col].kurtosis()

        elif np.issubdtype(df[col].dtype, np.number) and unique_count == 1 and dtype != 'boolean':
            col_stats['sample_value'] = sample_value
            col_stats['unique_count'] = unique_count
            col_stats['constant'] = True

        
        elif df[col].dtype == 'object' and dtype not in ['datetime', 'timeseries']:
            #col_stats['unique_categories'] = df[col].unique()
            col_stats['sample_value'] = sample_value
            col_stats['unique_count'] = unique_count
            col_stats['mode'] = df[col].mode().iloc[0]
            col_stats['category_counts'] = df[col].value_counts(dropna=False)
            if unique_count == 1:
                col_stats['constant'] = True

        elif dtype == 'boolean':
            value_counts = df[col].value_counts(dropna=True)
            col_stats['sample_value'] = sample_value
            col_stats['true_count'] = value_counts.get(1, 0)
            col_stats['false_count'] = value_counts.get(0, 0)
            if col_stats['true_count'] == 0 or col_stats['false_count'] == 0:
                col_stats['constant'] = True

        dtype_analysis[dtype]['columns'][col] = col_stats
        print(f"Processed column: {col}, Type: {dtype}, Unique Count: {unique_count}, Null Count: {null_count}")
    return dtype_analysis


def overview(df, dtype_analysis):
    '''Return an overview of the dataset quality and statistics'''
    print("Generating overview...")
    total_columns = len(df.columns)
    column_names = df.columns.tolist()
    dataframe_shape = df.shape
    dataframe_head = df.head()
    total_missing_values = df.isnull().sum().sum()
    dtype_counts = {dtype: type_info['count'] for dtype, type_info in dtype_analysis.items()}
    total_outliers_3sigma = 0
    outlier_columns = {}
    low_variance_columns = []
    high_cardinality_columns = []
    medium_cardinality_columns = []
    constant_columns = []
    skewness_values = []
    kurtosis_values = []
    # Loop through dtype_analysis to find columns with outliers, low variance, high cardinality, skewness, and kurtosis
    for dtype, type_info in dtype_analysis.items():
        for col, stats in type_info['columns'].items():
            if 'outliers' in stats:
                outliers_3sigma = stats['outliers'].get('> 3σ', 0)
                if outliers_3sigma > 0:
                    total_outliers_3sigma += outliers_3sigma
                    outlier_columns[col] = {'> 3σ': outliers_3sigma}
            
            # Identify low variance numerical columns (variance close to zero)
            if 'population_variance' in stats and stats['population_variance'] < 0.01:
                low_variance_columns.append(col)
            
            # Identify high cardinality categorical columns
            if 'unique_count' in stats and stats['unique_count'] > 50 and dtype == 'object':
                high_cardinality_columns.append(col)
            elif 'unique_count' in stats and stats['unique_count'] > 11 and 'unique_count' in stats and stats['unique_count'] < 50 and dtype == 'object':
                medium_cardinality_columns.append(col)

            if 'constant' in stats:
                constant_columns.append(col)
            
            # Collect skewness and kurtosis values
            if 'skewness' in stats:
                skewness_values.append(stats['skewness'])
            if 'kurtosis' in stats:
                kurtosis_values.append(stats['kurtosis'])
    
    duplicate_count = df.duplicated().sum()
    overview_data = {
        'total_columns': total_columns,
        'head': dataframe_head,
        'missing': total_missing_values,
        'column_names': column_names,
        'constant_columns_count': len(constant_columns),
        'dataframe_shape': dataframe_shape,
        'dtype_counts': dtype_counts,
        'duplicate_count': duplicate_count,
        'total_outliers_3sigma': total_outliers_3sigma,
        'outlier_columns': outlier_columns,
        'low_variance_columns': low_variance_columns,
        'high_cardinality_columns': high_cardinality_columns,
        'medium_cardinality_columns': medium_cardinality_columns,
        'skewness_range': (min(skewness_values), max(skewness_values)) if skewness_values else (None, None),
        'kurtosis_range': (min(kurtosis_values), max(kurtosis_values)) if kurtosis_values else (None, None),
    }
    print("Overview generated.")
    return overview_data

def data_quality_recommendations(df, overview_data, dtype_analysis):
    '''
    Returns in a accessable dictionary the recomendation data.
    '''
    print("Generating data quality recommendations...")
    recommendations = {}
    duplicate_recommendations = {}
    if overview_data['duplicate_count'] != 0:
        duplicate_recommendations['duplicate_row_count'] = overview_data['duplicate_count']
    if duplicate_recommendations:
        recommendations['Duplicate_Data'] = duplicate_recommendations
    print("Duplicate recommendations generated.")

    null_columns_dic = {}
    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        null_columns_dic['null_columns'] = null_columns
        null_columns_dic['null_column_count'] = len(null_columns)
        print("Null columns generated.")
        recommendations['null_columns'] = null_columns_dic


    missing_recommendations = {}
    if overview_data['missing'] != 0:
        missing_recommendations['total_missing_data'] = overview_data['missing']
        total_rows, total_columns = overview_data['dataframe_shape'][0], overview_data['dataframe_shape'][1]
        high_missing_data = {}
        regular_missing_data = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if (missing_count / total_rows)*100 > 30:
                high_missing_data[col] = {
                    'missing_count': missing_count,
                    'missing_percent': round((missing_count / total_rows)*100, 2)
                }
            elif (missing_count / total_rows)*100 < 30 and (missing_count / total_rows)*100 > 0: 
                regular_missing_data[col] = {
                    'missing_count': missing_count,
                    'missing_percent': round((missing_count / total_rows)*100, 2)
                }
        if high_missing_data:
            missing_recommendations['30%+_missing_data_columns'] = high_missing_data
        if regular_missing_data:
            missing_recommendations['0-29%_missing_data_columns'] = regular_missing_data
    if missing_recommendations:
        recommendations['missing_recommendations'] = missing_recommendations
    print("Missing recommendations generated.")  

    constant_recommendations = {}
    constant_columns = []
    if overview_data['constant_columns_count'] != 0:
        constant_recommendations['total_constant_columns'] = overview_data['constant_columns_count']
        for dtype, type_info in dtype_analysis.items():
            for col, stats in type_info['columns'].items():
                if 'constant' in stats:
                    constant_columns.append([col, stats['sample_value']])
        if constant_columns:
            constant_recommendations['constant_columns'] = constant_columns
    if constant_recommendations:
        recommendations['constant_recommendations'] = constant_recommendations
    print("Constant recommendations generated.")

    outlier_recommendations = {}
    if overview_data['total_outliers_3sigma'] != 0:
        outlier_recommendations['total_outliers'] = overview_data['total_outliers_3sigma']
        outlier_column_data = {}
        for dtype, dtype_info in dtype_analysis.items():
            for col_name, col_stats in dtype_info['columns'].items():
                if 'outliers' in col_stats:
                    outliers = col_stats['outliers']
                    outlier_info = {}
                    over_3 = outliers.get('> 3σ', 0)
                    over_4 = outliers.get('> 4σ', 0)
                    over_5 = outliers.get('> 5σ', 0)
                    from_3_to_4 = over_3 - over_4
                    from_4_to_5 = over_4 - over_5
                    from_5_plus = over_5
                    if over_3 > 0:
                        outlier_info['Total Outliers'] = over_3
                        outlier_info['3σ - 4σ'] = from_3_to_4
                        outlier_info['4σ - 5σ'] = from_4_to_5
                        outlier_info['5σ+'] = from_5_plus
                        outlier_info['plot'] = generate_outlier_plot(df, col_name)
                    if outlier_info:
                        outlier_column_data[col_name] = outlier_info
        if outlier_column_data:
            outlier_recommendations['outlier_columns'] = outlier_column_data
    if outlier_recommendations:
        recommendations['outlier_recommendations'] = outlier_recommendations
    print("Outlier recommendations generated.")

    skewness_recommendations = {}
    skew_range = overview_data.get('skewness_range', (None, None))
    if skew_range[0] is not None and skew_range[0] < -0.5 or skew_range[1] is not None and skew_range[1] > 0.5:
        skewness_recommendations['skewness_range'] = overview_data['skewness_range']
        skewed_columns = {}
        for dtype, dtype_info in dtype_analysis.items():
            for col_name, col_stats in dtype_info['columns'].items():
                if 'skewness' in col_stats:
                    skewness = col_stats['skewness']
                    if skewness > 0:
                        tail = 'right'
                    elif skewness < 0:
                        tail = 'left'
                    else:
                        tail = 'symmetric'
                    if skewness < -1:
                        bracket = 'severely left-skewed'
                    elif -1 <= skewness < -0.5:
                        bracket = 'moderately left-skewed'
                    elif -0.5 <= skewness <= 0.5:
                        bracket = 'approximately symmetric'
                    elif 0.5 < skewness <= 1:
                        bracket = 'moderately right-skewed'
                    elif skewness > 1:
                        bracket = 'severely right-skewed'
                    else:
                        bracket = 'symmetric'
                    
                    if bracket != 'approximately symmetric':
                        skewed_columns[col_name] = {
                            'skewness': round(skewness, 3),
                            'tail': tail,
                            'bracket': bracket,
                            'plot': generate_skewness_plot(df, col_name)
                        }
        if skewed_columns:
            skewness_recommendations['skewed_columns'] = skewed_columns
    if skewness_recommendations:
        recommendations['skewness_recommendations'] = skewness_recommendations
    print("Skewness recommendations generated.")

    cardinality_recommendations = {}
    if overview_data['high_cardinality_columns'] or overview_data['medium_cardinality_columns']:
        loops = ['high_cardinality_columns', 'medium_cardinality_columns']
        for loop in loops:
            columns = overview_data[loop]
            if columns:
                cardinality_recommendations[loop] = {}
                for col in columns:
                    cardinality_recommendations[loop][col] = df[col].nunique()
    if cardinality_recommendations:
        recommendations['cardinality_recommendations'] = cardinality_recommendations
    print("Cardinality recommendations generated.")

    variance_recommendations = {}
    low_variance_numeric_columns = {}
    low_variance_categorical_columns = {}
    low_variance_boolean_columns = {}
    for dtype, dtype_info in dtype_analysis.items():
        for col_name, col_stats in dtype_info['columns'].items():
            if dtype in ['float64', 'int64'] and 'population_variance' in col_stats:
                if col_stats['population_variance'] < 0.01:
                    low_variance_numeric_columns[col_name] = round(col_stats['population_variance'], 6)
            elif dtype == 'object' and 'category_counts' in col_stats:
                total = sum(col_stats['category_counts'].values)
                top_category = col_stats['category_counts'].idxmax()
                top_freq = col_stats['category_counts'].max()
                top_percent = (top_freq / total) * 100
                if top_percent > 85:
                    low_variance_categorical_columns[col_name] = {
                        'most_common_category': top_category,
                        'percentage_of_total': round(top_percent, 2)
                    }
            elif dtype == 'boolean' and 'true_count' in col_stats and 'false_count' in col_stats:
                total = col_stats['true_count'] + col_stats['false_count']
                if total > 0:
                    dominant_percent = max(col_stats['true_count'], col_stats['false_count']) / total * 100
                    if dominant_percent > 85:
                        low_variance_boolean_columns[col_name] = {
                            'dominant_value': col_stats['true_count'] > col_stats['false_count'],
                            'percentage_of_total': round(dominant_percent, 2)
                        }
    if low_variance_numeric_columns:
        variance_recommendations['low_variance_numeric_columns'] = low_variance_numeric_columns
    if low_variance_categorical_columns:
        variance_recommendations['low_variance_categorical_columns'] = low_variance_categorical_columns
    if low_variance_boolean_columns:
        variance_recommendations['low_variance_boolean_columns'] = low_variance_boolean_columns
    if variance_recommendations:
        recommendations['variance_recommendations'] = variance_recommendations
    print("Variance recommendations generated.")

    imbalanced_boolean_columns = {}
    for dtype, type_info in dtype_analysis.items():
        if dtype == 'boolean':
            for col_name, col_stats in type_info['columns'].items():
                true_count = col_stats.get('true_count', 0)
                false_count = col_stats.get('false_count', 0)
                total = true_count + false_count
                if total == 0:
                    continue
                dominant_value = 1 if true_count > false_count else 0
                dominant_percentage = max(true_count, false_count) / total * 100
                if dominant_percentage >= 70:
                    fig, ax = plt.subplots(figsize=(6, 1))
                    ax.barh([""], [false_count], color='#ff7f0e', label='False')
                    ax.barh([""], [true_count], left=[false_count], color='#1f77b4', label='True')
                    ax.set_xlim(0, total)
                    ax.set_title(f"{col_name} — {round(dominant_percentage)}% {bool(dominant_value)}", fontsize=10)
                    ax.axis('off')
                    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
                    buf = BytesIO()
                    plt.tight_layout()
                    plt.savefig(buf, format='png', bbox_inches='tight')
                    plt.close(fig)
                    encoded_img = base64.b64encode(buf.getvalue()).decode('utf-8')
                    imbalanced_boolean_columns[col_name] = {
                        'dominant_value': bool(dominant_value),
                        'percentage_of_total': round(dominant_percentage, 2),
                        'plot': encoded_img
                    }
    if imbalanced_boolean_columns:
        recommendations['imbalanced_boolean_columns'] = imbalanced_boolean_columns
        print('Boolean Class recommendations generated.')

    correlation_recommendations = {}
    numeric_corr = {}
    numeric_high_corr = {}
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[0] > 10000:
        numeric_df = numeric_df.sample(10000, random_state=42)
        correlation_recommendations['pearson_sampled'] = True

    corr_matrix = numeric_df.corr().abs()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    corr_matrix_rounded = corr_matrix.round(2)
    plt.figure(figsize=(25, 15))
    heatmap = sns.heatmap(corr_matrix_rounded, annot=True, cmap="coolwarm", mask=mask, linewidths=0.5, 
                      linecolor='white', annot_kws={"size": 12})
    plt.title("Numeric Variables Correlation Heatmap (Rounded 2 Decimal Places)", fontsize=18)
    plt.xticks(rotation=45, ha='right', fontsize=14)
    plt.yticks(rotation=0, fontsize=14)
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    corr_heatmap_base64 = base64.b64encode(img_buf.read()).decode('utf-8')

    
    tri_df = corr_matrix.where(~mask)
    high_corr = tri_df.stack().reset_index()
    high_corr.columns = ['Feature 1', 'Feature 2', 'Correlation']
    high_corr = high_corr[high_corr['Correlation'] >= 0.7]
    numeric_high_corr = {
        f"{row['Feature 1']} & {row['Feature 2']}": round(row['Correlation'],2)
        for _, row in high_corr.iterrows()
    }
    if numeric_high_corr:
            numeric_corr = {
                'total_high_numeric_corr': len(numeric_high_corr),
                'numeric_high_corr': numeric_high_corr,
                'corr_heatmap_base64': corr_heatmap_base64
            }
            correlation_recommendations['numeric_corr'] = numeric_corr
            print("Numeric correlation recommendations generated.")
    categorical_df = df.select_dtypes(include=['object', 'bool']).astype(str)
    if categorical_df.shape[0] > 10000:
        categorical_df = categorical_df.sample(10000, random_state=42)
        correlation_recommendations['cramersv_sampled'] = True
    categorical_columns = categorical_df.columns.tolist()
    categorical_high_corr = {}
    for i in range(len(categorical_columns)):
        for j in range(i + 1, len(categorical_columns)):
            col1 = categorical_columns[i]
            col2 = categorical_columns[j]
            confusion_matrix = pd.crosstab(categorical_df[col1], categorical_df[col2])
            if confusion_matrix.size == 0:
                continue
            chi2 = chi2_contingency(confusion_matrix, correction=False)[0]
            n = confusion_matrix.sum().sum()
            phi2 = chi2 / n if n > 0 else 0
            r, k = confusion_matrix.shape
            phi2_corr = max(0, phi2 - ((k - 1)*(r - 1))/(n - 1)) if n > 1 else 0
            r_corr = r - ((r - 1)**2)/(n - 1) if n > 1 else 0
            k_corr = k - ((k - 1)**2)/(n - 1) if n > 1 else 0
            denom = min((k_corr - 1), (r_corr - 1))
            cramer_v = np.sqrt(phi2_corr / denom) if denom > 0 else 0
            if cramer_v >= 0.7:
                key = f"{col1} & {col2}"
                categorical_high_corr[key] = round(cramer_v, 2)
    if categorical_high_corr:
        categorical_corr = {
            'total_high_categorical_corr': len(categorical_high_corr),
            'categorical_high_corr': categorical_high_corr
        }
        correlation_recommendations['categorical_corr'] = categorical_corr  
        print("Categorical correlation recommendations generated.")

    if correlation_recommendations:
        recommendations['correlation_recommendations'] = correlation_recommendations
        print("Correlation recommendations generated.")

    VIF_recommendations = {}
    VIF_df = df.copy().select_dtypes(include=['float64', 'int64'])
    if VIF_df.shape[0] > 10000:
        VIF_df = VIF_df.sample(10000, random_state=42)
        VIF_recommendations['sampled'] = True
    constant_cols = [col for col in VIF_df.columns if VIF_df[col].nunique() <= 1]
    if constant_cols:
        VIF_recommendations['constant_columns_removed'] = constant_cols
        VIF_df = VIF_df.drop(columns=constant_cols)
    all_null_cols = VIF_df.columns[VIF_df.isnull().all()].tolist()
    if all_null_cols:
        VIF_recommendations['Null_columns_removed'] = all_null_cols
        VIF_df = VIF_df.drop(columns=all_null_cols)
    null_fraction = VIF_df.isnull().mean()
    high_null_cols = null_fraction[null_fraction > 0.4].index.tolist()
    if high_null_cols:
        VIF_recommendations['High_Null_columns_removed'] = high_null_cols
        VIF_df = VIF_df.drop(columns=high_null_cols)
    remaining_null_cols = VIF_df.columns[VIF_df.isnull().any()].tolist()
    if remaining_null_cols:
       VIF_recommendations['Imputed_columns'] = remaining_null_cols
       VIF_df[remaining_null_cols] = VIF_df[remaining_null_cols].fillna(VIF_df[remaining_null_cols].mean())
    if VIF_df.shape[1] < 2:
        VIF_recommendations['numeric_column_size_error'] = 'Not enough Numeric Columns for VIF Analysis'
    else:
        X = add_constant(VIF_df)
        vif_medum_result = {}
        vif_highresult = {}
        for i in range(1, X.shape[1]):  
            vif = variance_inflation_factor(X.values, i)
            if vif >= 5 and vif < 10:
                vif_medum_result[X.columns[i]] = vif
            elif vif > 10:
                vif_highresult[X.columns[i]] = vif
        if vif_medum_result:
            VIF_recommendations['medium_VIF'] = vif_medum_result
        if vif_highresult:
            VIF_recommendations['high_VIF'] = vif_highresult
    
    if VIF_recommendations:
        recommendations['VIF_recommendations'] = VIF_recommendations
        print("VIF Recommendations generated.")
        

    
    print("Data quality recommendations generated.")
    return recommendations

