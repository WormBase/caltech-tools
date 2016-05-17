#!/usr/bin/perl 

# flat file for genes is not on cronjob.  this machine probably does not have tazendra access, copied from .204  2016 03 24

use CGI;
use strict;
use LWP::Simple;
use LWP::UserAgent;
use Time::HiRes qw( time );

my $startTime = time; my $prevTime = time;
$startTime =~ s/(\....).*$/$1/;
$prevTime  =~ s/(\....).*$/$1/;

# use DBI;
# my $dbh = DBI->connect ( "dbi:Pg:dbname=testdb;host=131.215.52.76", "", "") or die "Cannot connect to database!\n";     # for remote access
# # my $dbh = DBI->connect ( "dbi:Pg:dbname=wobrdb", "", "") or die "Cannot connect to database!\n";
# my $result;

my $query = new CGI;
my $base_solr_url = 'http://wobr.caltech.edu:8082/solr/';		# raymond dev URL 2015 07 24

my $title = 'Tissue Enrichment Analysis';
my ($header, $footer) = &cshlNew($title);
&process();

sub process {
  my $action;                   # what user clicked
  unless ($action = $query->param('action')) { $action = 'none'; }

  if ($action eq 'anatomySobaInput')           { &anatomySobaInput();      }
    elsif ($action eq 'Analyze List')          { &anatomySoba('textarea'); }
    elsif ($action eq 'Analyze File')          { &anatomySoba('file');     }
    else { &anatomySobaInput(); }				# no action, show dag by default
} # sub process


sub anatomySobaInput {
  &printHtmlHeader(); 
#   print qq(<h1>Tissue Enrichment Analysis <a href="http://wiki.wormbase.org/index.php/User_Guide/TEA" target="_blank"><span style="font-size:12pt; text-decoration: underline;">?</span></a></h1>);
  print qq(<h1>Tissue Enrichment Analysis <a href="http://wiki.wormbase.org/index.php/User_Guide/TEA" target="_blank"><img src="images/info.gif"></a></h1>);
  print qq(Discovering association between a gene group and anatomical parts.<br/><br/>);
  print qq(<form method="post" action="tea.cgi" enctype="multipart/form-data">);
  print qq(<table cellpadding="8"><tr><td>);
  print qq(Enter a list of C. elegans gene names in the box<br/>);
  print qq(<textarea name="genelist" rows="20" cols="60" onkeyup="if(this.value != '') { document.getElementById('geneNamesFile').disabled = 'disabled'; document.getElementById('analyzeFileButton').disabled = 'disabled'; } else { document.getElementById('geneNamesFile').disabled = ''; document.getElementById('analyzeFileButton').disabled = ''; }"></textarea><br/>);
#   print qq(<input Type="checkbox" name="showProcessTimes" Value="showProcessTimes">Show Process Times<br/>\n);
#   print qq(<input Type="checkbox" name="convertGeneToId" Value="convertGeneToId">Convert Genes to IDs<br/>\n);	# don't need this anymore, will figure out whether it needs to convert based on whether any non-WBGene IDs are in the input
  print qq(<input type="submit" name="action" id="analyzeListButton" value="Analyze List"><br/><br/><br/>);
  print qq(</td><td valign="top"><p>or</p><br/>\n);
  print qq(</td><td valign="top">);
  print qq(Upload a file with gene names<br/>);
  print qq(<input type="file" name="geneNamesFile" id="geneNamesFile"/><br/>);
  print qq(<input type="submit" name="action" id="analyzeFileButton" value="Analyze File"><br/>\n);
  print qq(</td></tr></table>);
#  print qq(<span style="font-size: 10pt;">Enter a gene list consisting of any accepted C. elegans gene names separated by spaces, colons or tabs into the box. Alternatively, input a plain-text file of gene names separated by spaces, colons or tabs using the 'Choose file' button. Text files must be plain text (.txt).<br/>The program returns enriched tissues as assessed by a hypergeometric function, after FDR correction. A bar chart containing the top 15 enriched tissues, sorted by increasing q-value and by decreasing fold-change is automatically generated. Bar coloring is intended to improve readability, and color does not convey information.<br/></span>\n);
  print qq(</form>);
#   &printMessageFooter(); 		# raymond wanted to remove this 2016 04 14
  &printHtmlFooter(); 
} # sub anatomySobaInput

sub anatomySoba {
  my ($filesource) = @_;
  &printHtmlHeader(); 
  print qq(<h1>Tissue Enrichment Analysis Results <a href="http://wiki.wormbase.org/index.php/User_Guide/TEA" target="_blank"><img src="images/info.gif"></a></h1>);
    print qq(Return up to 15 most significant anatomy terms.<br/><br/>);

  my ($var, $datatype)          = &getHtmlVar($query, 'datatype');
#   ($var, my $showProcessTimes)  = &getHtmlVar($query, 'showProcessTimes');
#   ($var, my $convertGeneToId)   = &getHtmlVar($query, 'convertGeneToId');	# don't need this anymore, will figure out whether it needs to convert based on whether any non-WBGene IDs are in the input
  ($var, my $calculateLcaNodes) = &getHtmlVar($query, 'calculateLcaNodes');
#   my ($var, $download)    = &getHtmlVar($query, 'download');
  unless ($datatype) { $datatype = 'anatomy'; }			# later will need to change based on different datatypes

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Loading dictionary"); print qq($message<br/>\n); }

# python3  /home/raymond/local/src/git/TissueEnrichmentAnalysis/hypergeometricTests.py  /home/raymond/local/src/git/dictionary_generator/anat_dict.csv  /home/raymond/local/src/git/TissueEnrichmentAnalysis/input/SCohen_daf22.csv -p -s -t "BLAH"

  my %dict;
  my $dictFile = '/home/raymond/local/src/git/dictionary_generator/anat_dict.csv';
  open (DICT, "<$dictFile") or die "Cannot open $dictFile : $!";
  while (my $line = <DICT>) {
    my (@stuff) = split/,/, $line;
    if ($stuff[0] =~ m/WBGene/) { $dict{$stuff[0]}++; }
  } # while (my $line = <DICT>)
  close (DICT) or die "Cannot close $dictFile : $!";

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Getting altId mappings"); print qq($message<br/>\n); }

  my @annotAnatomyTerms;					# array of annotated terms to loop and do pairwise comparisons
  my $genelist = '';
  if ($filesource eq 'textarea') {
      ($var, $genelist) = &getHtmlVar($query, 'genelist'); }
    elsif ($filesource eq 'file') {
      my $upload_filehandle = $query->upload("geneNamesFile");
      while ( <$upload_filehandle> ) { $genelist .= $_; }
    }
  if ($genelist =~ m/,/) { $genelist =~ s/,/ /g; }
  my (@names) = split/\s+/, $genelist;
  my $hasNonWBGene = 0;
  foreach (@names) { if ($_ !~ m/WBGene/i) { $hasNonWBGene++; } }
  my $convertGeneToId = 0;
  if ($hasNonWBGene) { $convertGeneToId++; }

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Getting postgres gene name mappings"); print qq($message<br/>\n); }
  my %geneNameToId; my %geneIdToName;
  if ($convertGeneToId) {
#     my ($geneNameToIdHashref, $geneIdToNameHashref) = &populateGeneNamesFromPostgres();
    my ($geneNameToIdHashref, $geneIdToNameHashref) = &populateGeneNamesFromFlatfile();
    %geneNameToId        = %$geneNameToIdHashref;
    %geneIdToName        = %$geneIdToNameHashref; }

#   my %geneAnatomy; my %anatomyGene;

#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Processing user genes for validity"); print qq($message<br/>\n); }
  unless ($convertGeneToId) { foreach my $name (@names) { $geneNameToId{lc($name)} = $name; $geneIdToName{$name} = $name; } }
  my @invalidGene; my @nodataGene; my @goodGene; 
  foreach my $name (@names) {
    my ($lcname) = lc($name);
    my $wbgene = '';
    if ($geneNameToId{$lcname}) {
        $wbgene = $geneNameToId{$lcname}; 
        if ($dict{$wbgene}) { push @goodGene, $wbgene; }
          else { push @nodataGene, $wbgene; } }
      else { push @invalidGene, $name; }
  } # foreach my $name (@names)

  my %anatomyTerms;
  if (scalar @goodGene > 0) {
#       if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Processing hgf"); print qq($message<br/>\n); }
      my $time = time;
      my $tempfile     = '/tmp/hyperGeo/hyperGeo' . $time;
      my $tempOutFile  = '/tmp/hyperGeo/hyperGeo' . $time . '.txt';
#       my $tempOutUrl   = '../data/hyperGeo/hyperGeo' . $time . '.txt';	# changed data to not be in other parent directory
      my $tempOutUrl   = 'data/hyperGeo/hyperGeo' . $time . '.txt';
      open (OUT, ">$tempOutFile") or die "Cannot open $tempOutFile : $!";
#       my $tempImageUrl = '../data/hyperGeo/hyperGeo' . $time . '.svg';	# changed data to not be in other parent directory
      my $tempImageUrl = 'data/hyperGeo/hyperGeo' . $time . '.svg';
      open (TMP, ">$tempfile") or die "Cannot open $tempfile : $!";
#       print TMP qq(gene,reads\n);
      foreach my $gene (@goodGene) { print TMP qq($gene\n); }
      close (TMP) or die "Cannot close $tempfile : $!";
#       my $hyperData = `python /home/raymond/local/src/git/tissue_enrichment_tool_hypergeometric_test/src/hypergeometricTests.py /home/azurebrd/local/src/git/tissue_enrichment_tool_hypergeometric_test/genesets/WBPaper00013489_Ray_Enriched_WBbt:0006941_25`;
#       my $hyperData = `python /home/azurebrd/public_html/cgi-bin/hypergeometricTests.py /home/azurebrd/local/src/git/tissue_enrichment_tool_hypergeometric_test/genesets/WBPaper00013489_Ray_Enriched_WBbt:0006941_25`;
#       my $hyperData = `python /home/azurebrd/public_html/cgi-bin/hypergeometricTests.py $tempfile`;
#       my $hyperData = `python /home/raymond/local/src/git/tissue_enrichment_tool_hypergeometric_test/src/hypergeometricTests.py $tempfile`;
#                      python3  /home/raymond/local/src/git/TissueEnrichmentAnalysis/hypergeometricTests.py  /home/raymond/local/src/git/dictionary_generator/anat_dict.csv  /home/raymond/local/src/git/TissueEnrichmentAnalysis/input/SCohen_daf22.csv -p -s -t "BLAH"
      my $hyperData = `/home/raymond/local/src/git/TissueEnrichmentAnalysis/bin/tea  -d /home/raymond/local/src/git/dictionary_generator/anat_dict.csv  $tempfile "$tempfile" -p -s`;

#       `rm $tempfile`;
# print qq(HPD $hyperData HPD<br/>);
#       ($hyperData) = $hyperData =~ m/------------------------\n(.*?)------------------------/ms;
#       if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Processing hgf results to display"); print qq($message<br/>\n); }
      my (@hyperData) = split/\n/, $hyperData;
#       my $header = shift @hyperData;
#       my (@header) = split/,/, $header;
#       my $th = join"</th><th>", @header;
      if (scalar @hyperData > 0) {
#           print qq(<table><tr><th>$th</th></tr>\n);
          print qq(<table border="1" style="border-spacing: 0;">);  
          foreach my $line (@hyperData) {
            next if ($line =~ m/Executing script/);
            if ($line) {
              print OUT qq($line\n);
              $line =~ s|\t|</td><td>|g;
              if ($line =~ m/(WBbt:\d+)/) { 
                my $wbbt = $1;
                my $url = 'http://www.wormbase.org/species/all/anatomy_term/' .$wbbt . '#013--10';
                $line =~ s/$wbbt/<a href="$url" target="_blank">$wbbt<\/a>/; }
              print qq(<tr><td align="right">$line</td></tr>);
            }
          } # foreach my $line (@hyperData)
          print qq(</table>);  
        }
        else { print qq(No significantly enriched cell/tissue has been found.<br/>\n); }
      close (OUT) or die "Cannot close $tempOutFile : $!";
      print qq(<img src="$tempImageUrl"><br/>\n);
#      print qq(This bar chart automatically displays up to 15 enriched tissues sorted by q-value (lowest q-value on top) and secondarily by fold-change (higher fold change on top) in case of tied q-values. Colors are meant to improve readability and do not convey information.<br/>);
      print qq(Drag graph to your desktop to save.<br/>);
      print qq(Download output table <a href="$tempOutUrl" target="_blank">here</a><br/><br/>);
    }
    else { print qq(There are no genes with annotated data to generate results.<br/>\n); }
  print qq(<br/>);
#   if ($showProcessTimes) { (my $message) = &getDiffTime($startTime, $prevTime, "Displaying gene sets"); print qq($message<br/>\n); }
  if (scalar @invalidGene > 0) {
    my $countInvalidGenes = scalar @invalidGene;
    print qq(Your list has $countInvalidGenes invalid WormBase genes :<br/>\n);
    print qq(<textarea rows="6" cols="80">);
    foreach my $gene (@invalidGene) { print qq($gene\n); } 
    print qq(</textarea><br/><br/>); }
  if (scalar @nodataGene > 0) {
    my $countNodataGenes = scalar @nodataGene;
    print qq(Your list has $countNodataGenes valid WormBase genes that have no annotated data or are excluded from testing :<br/>\n);
    print qq(<textarea rows="6" cols="80">);
    foreach my $gene (@nodataGene) { print qq($gene - $geneIdToName{$gene}\n); } 
    print qq(</textarea><br/><br/>); }
  if (scalar @goodGene > 0) {
    my $countGoodGenes = scalar @goodGene;
    print qq(Your list has $countGoodGenes valid WormBase genes included in statistical testing :<br/>\n);
    print qq(<textarea rows="6" cols="80">);
    foreach my $gene (@goodGene) { print qq($gene - $geneIdToName{$gene}\n); } 
    print qq(</textarea><br/><br/>); }
  print qq(<a href="tea.cgi">perform another query</a><br/>);

#   &printMessageFooter(); 		# raymond wanted to remove this 2016 04 14
  &printHtmlFooter(); 
# http://131.215.12.204/~azurebrd/cgi-bin/amigo.cgi?genelist=WBGene00010209+WBGene00010212+WBGene00010295+WBGene00015814+WBGene11111111+WBGene00000012+WBGene00000013+WBGene00000002+ZK512.6%0D%0A&action=anatomySoba
# http://131.215.12.204/~azurebrd/cgi-bin/amigo.cgi?action=anatomySobaInput
# WBGene00010209 WBGene00010212 WBGene00010295 WBGene00015814 WBGene11111111 WBGene00000012 WBGene00000013 WBGene00000002 ZK512.6 qwera 2z3zt daf-2
} # sub anatomySoba


sub populateGeneNamesFromFlatfile {
  my %geneNameToId; my %geneIdToName;
  my $infile = '/home/azurebrd/cron/gin_names/gin_names.txt';
  open (IN, "<$infile") or die "Cannot open $infile : $!";
  while (my $line = <IN>) {
    chomp $line;
    my ($id, $name, $primary) = split/\t/, $line;
    if ($primary eq 'primary') { $geneIdToName{$id}     = $name; }
    my ($lcname)           = lc($name);
    $geneNameToId{$lcname} = $id; }
  close (IN) or die "Cannot close $infile : $!";
  return (\%geneNameToId, \%geneIdToName);
} # sub populateGeneNamesFromFlatfile


sub printMessageFooter { print qq(if you use this tool, please cite us. If you have ideas, requests or bug-issues, please contact <a href="mailto:dangeles\@caltech.edu">dangeles\@caltech.edu</a><br/>); }

# sub printHtmlFooter { print qq(</body></html>\n); }
sub printHtmlFooter { print $footer }

sub printHtmlHeader { 
  my $javascript = << "EndOfText";
<script src="http://code.jquery.com/jquery-1.9.1.js"></script>
<script type="text/javascript">
function toggleShowHide(element) {
    document.getElementById(element).style.display = (document.getElementById(element).style.display == "none") ? "" : "none";
    return false;
}
function togglePlusMinus(element) {
    document.getElementById(element).innerHTML = (document.getElementById(element).innerHTML == "&nbsp;+&nbsp;") ? "&nbsp;-&nbsp;" : "&nbsp;+&nbsp;";
    return false;
}
</script>
EndOfText
#   print qq(Content-type: text/html\n\n<html><head><title>Tissue Enrichment Analysis</title>$javascript</head><body>\n); 
  print qq(Content-type: text/html\n\n$header $javascript<body>\n); 
}

sub getHtmlVar {                
  no strict 'refs';             
  my ($query, $var, $err) = @_; 
  unless ($query->param("$var")) {
    if ($err) { print "<FONT COLOR=blue>ERROR : No such variable : $var</FONT><BR>\n"; }
  } else { 
    my $oop = $query->param("$var");
    $$var = &untaint($oop);         
    return ($var, $$var);           
  } 
} # sub getHtmlVar

sub untaint {
  my $tainted = shift;
  my $untainted;
  if ($tainted eq "") {
    $untainted = "";
  } else { # if ($tainted eq "")
    $tainted =~ s/[^\w\-.,;:?\/\\@#\$\%\^&*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]//g;
    if ($tainted =~ m/^([\w\-.,;:?\/\\@#\$\%&\^*\>\<(){}[\]+=!~|' \t\n\r\f\"€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•—˜™š›œžŸ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ]+)$/) {
      $untainted = $1;
    } else {
      die "Bad data Tainted in $tainted";
    }
  } # else # if ($tainted eq "")
  return $untainted;
} # sub untaint

sub cshlNew {
  my $title = shift;
  unless ($title) { $title = ''; }      # init title in case blank
  my $page = get "http://tazendra.caltech.edu/~azurebrd/sanger/wormbaseheader/WB_header_footer.html";
#  $page =~ s/href="\//href="http:\/\/www.wormbase.org\//g;
#  $page =~ s/src="/src="http:\/\/www.wormbase.org/g;
  ($header, $footer) = $page =~ m/^(.*?)\s+DIVIDER\s+(.*?)$/s;  # 2006 11 20    # get this from tazendra's script result.
#   $header =~ s/WormBase - Home Page/$title/g;                 # 2015 05 07    # wormbase 2.0
  $header =~ s/<title>.*?<\/title>/<title>$title<\/title>/g;
  return ($header, $footer);
} # sub cshlNew

