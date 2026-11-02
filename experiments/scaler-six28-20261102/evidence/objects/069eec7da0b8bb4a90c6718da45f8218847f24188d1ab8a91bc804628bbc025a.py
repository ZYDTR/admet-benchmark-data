import json,csv
from pathlib import Path
import argparse, tempfile
parser=argparse.ArgumentParser(); parser.add_argument('--output-dir',type=Path)
args=parser.parse_args(); D=args.output_dir or Path(tempfile.mkdtemp(prefix='admet-feature-algebra-')); E=D/'evidence'; C=D/'checks'; E.mkdir(parents=True,exist_ok=True); C.mkdir(parents=True,exist_ok=True)
# Transcription of N18 aggregate fields; never individual labels or residuals.
cols=['task','train_n','valid_n','test_n','used_sd_min','used_sd_lt1e5','used_sd_lt1e3','fit_z_max','stop_z_max','valid_z_max','valid_rows_gt100','valid_rows_gt1000','valid_rowmax_median','valid_rowmax_p99','test_z_max','test_rows_gt100','test_rows_gt1000']
data=[
['bbb_martins',1421,203,406,3.249378642067313e-5,0,20,35.74914748984693,625.337754202369,368.62744664693196,2,0,8.91184871583243,65.1403407702768,12137.599478934742,48,6],
['clearance_hepatocyte_az',848,122,243,3.449192263360601e-6,1,71,27.586464521106763,162.18826227822498,255.01390924974163,3,0,7.731130979755413,225.42325483323313,8251.408452994334,5,3],
['cyp2d6_veith',9191,1313,2626,4.6381508582271636e-5,0,11,90.94699870904051,333.68663765603054,274.45158495150156,6,0,7.522174864990189,66.06339904226833,400.8395297337054,16,0],
['ld50_zhu',3970,1937,1478,1.1447474207670894e-5,0,14,59.76686787006388,541.4563904231259,85887.20785219701,137,25,23.38035885974054,2138.9622701332096,690.6793467939129,12,0],
['lipophilicity_astrazeneca',2940,420,840,1.4511601875710767e-6,2,51,51.430211429409134,2982.536819942199,235.38212294567606,1,0,8.018907144403252,59.32280169722062,17773.138288071877,6,2],
['solubility_aqsoldb',5045,2940,1997,1.2254838566150283e-6,2,13,67.37848939349523,71.7451518197462,8886.414669464164,445,50,25.515360397349816,6417.958840720711,3354.3978374797225,10,3]]
rows=[dict(zip(cols,x)) for x in data]
for r in rows:
 r['valid_fraction_gt1000']=r['valid_rows_gt1000']/r['valid_n'];r['valid_fraction_gt100']=r['valid_rows_gt100']/r['valid_n'];r['source']='N18'
(E/'feature-summary-transcription.json').write_text(json.dumps({'representation':'aggregate transcription, not original bytes; not independent raw-array recomputation','source':'N18','rows':rows},ensure_ascii=False,indent=2))
with (C/'feature-summary.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Algebra on published summary; no model evaluations, no feature-row reconstruction.
dims=[('ld50_zhu','valid',767,85887.20785219701,1.9153966945850698e-7,1.1447474207670894e-5),('ld50_zhu','valid',1279,5970.0364786091195,2.1252624264889164e-6,.00012701780360657722),('solubility_aqsoldb','valid',1120,8886.414669464164,2.883349225157872e-6,.00010504441161174327),('solubility_aqsoldb','valid',928,3450.416620286741,2.4329994630534202e-5,.0004323538450989872),('solubility_aqsoldb','valid',1774,2269.4358548618175,9.881986784421315e-8,6.6586558205017354e-6),('lipophilicity_astrazeneca','test',1221,17773.138288071877,4.8864009727367375e-8,1.4511601875710767e-6)]
a=[]
for task,split,dim,z,mu,sd in dims:
 a.append({'task':task,'split':split,'dimension_zero_based':dim,'source':'N18','published_max_abs_z':z,'fit_mean':mu,'fit_sd_used':sd,'derived_max_abs_x_minus_mu':z*sd,'hypothetical_denominator_only_max_abs_z':{str(tau):z*sd/max(sd,tau) for tau in [1e-5,1e-3,1e-2]},'limitation':'Fixed-feature denominator algebra only; not trained model or prediction improvement, not global maximum after transformation.'})
(C/'extreme-dimension-algebra.json').write_text(json.dumps(a,indent=2))
counts={'current_train_sum':sum(x['train_n'] for x in rows),'current_valid_sum':sum(x['valid_n'] for x in rows),'current_test_sum':sum(x['test_n'] for x in rows)}
counts['all_partitions_four_config_prediction_rows']=4*sum(counts.values());counts['current_valid_four_config_rows']=4*counts['current_valid_sum'];counts['source']='N18 and N08; source counts independently summed, files not physically row-counted'
assert counts['all_partitions_four_config_prediction_rows']==151760
(C/'partition-count-crosscheck.json').write_text(json.dumps(counts,indent=2))
print(counts)
