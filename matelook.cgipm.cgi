#!/usr/bin/perl -w

# written by andrewt@cse.unsw.edu.au September 2016
# as a starting point for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/matelook/

use CGI qw/:all/;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;

sub main() {
	# print start of HTML ASAP to assist debugging if there is an error in the script
	print page_header();
	
	# Now tell CGI::Carp to embed any warning in HTML
	warningsToBrowser(1);
	
	# define some global variables
	$debug = 1;
	$users_dir = "dataset-medium";
	
	print user_page();
	print page_trailer();
}


#
# Show unformatted user for user "n".
# Increment parameter n and store it as a hidden variable
#
sub user_page {
    my $n = param('n') || 0;
    my @users = sort(glob("$users_dir/*"));
    my $user_to_show  = $users[$n % @users];
    my $user_filename = "$user_to_show/user.txt";
    open my $p, "$user_filename" or die "can not open $user_filename: $!";
    $user = join '', <$p>;
    close $p;
    param('n', $n + 1);
    return div({-class => "matelook_user_details"}, "\n$user\n"), "\n",
        '<p>'.
        start_form, "\n",
        hidden('n'), "\n",
        submit({-class => "matelook_button", -value => 'Next user'}), "\n",
        end_form, "\n";
}


#
# HTML placed at the top of every page
#
sub page_header {
    return header(-charset => "utf-8"),
        start_html(-title => 'matelook', -style => "matelook.css"),
        div({-class => "matelook_heading"}, "matelook");
}


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

main();

