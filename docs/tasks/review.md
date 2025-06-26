# The Review Process

## Overview

On a high-level, the review process of the proposals for a conference works as follows:

1. find external reviewers and learn about their preferences,
2. onboard reviewers in [Pretalx],
3. assign proposals to reviewers according to their preferences,
4. communicate with the reviewers occasionally for updates,
5. track the whole process.

## 1. Find External Reviewers and Learn about their Preferences

For the PyConDE / PyData Berlin 2023, we were looking for about 50 external reviewers since we expected about 400
proposals, and we wanted to have 3 reviews per proposal. This would amount to about 25 proposals to review per person, which
is manageable within a few weeks if you schedule 5-15 minutes per proposal.

To get external reviewers, we decided that would only ask within our (Program Committee members') circle of trust and refer them to [Google Forms]. The form
basically consisted of following questions with descriptions:

* **Name** \[short answer\]: Please write your name starting with your first name, e.g. Albert Einstein.
* **Affiliation** \[short answer\]: Please state the name or organisation you are affiliated with.
* **Who do you know from the Committee?** \[short answer\]: We believe in the ring of trust model. With this question, we really only
  want to make sure that random people are not signing up with no connection to any member of the Program Committee.
* **Availability during the Review Period** \[checkboxes]: The bulk of the review work will take place from January 5th to February
  13th, 2023, so it is important that you are broadly available during this period. That being said, you will be quite
  flexible in managing your time but being on vacation with no internet for 3 weeks might be suboptimal here ;-)
  *There was only one mandatory checkbox: Yes, I am broadly available during this period.*
* **Additional comments regarding your availability during the review period.** \[long answer\]
* **Topics you want to review**: These are the topics you are interested in reviewing. The more you select the better.
  Don't be shy, you don't have to be an expert in a topic to review a proposal. If you are interested in a topic and
  have some knowledge about it, you are totally up for the job :-)
  *Each track in Pretalx corresponded to one checkbox in this form. At least 5 preferences needed to be chosen.*
* **Do you want your name to be listed as a reviewer on the conference website?** \[checkbox\] *Mandatory yes/no checkboxes*
* **Any additional comments for the Program Committee** \[long answer\]

!!! tip
    * [Google Form] will use the separator `, ` (comma, whitespace) for the selected checkboxes. Having the same separator
      in your track name, e.g. "General: Community, Diversity, Career, Life and everything else", will make it a bit harder
      to parse the resulting [Google Sheet]. So it's better to avoid them in track names.
    * Depending on how you want to assign proposals to reviewers later, it might also make sense to ask the reviewers if
      they only want to be assigned a single batch, or if they are also interested in getting more proposals to review after
      their batch is done.

Every submission of the Google Form is then automatically added to a Google Sheet, let's call it the *volunteer sheet*, which can be easily read with the
help of Pytanis. Check out our [Google Sheet docs](../usage/gsheet.md) and [Pytanis' google module] to learn about more functionality.


## 2. Onboard Reviewers in Pretalx

In Pretalx select <kbd>Organisers</kbd> in the left menu bar (you need Admin-rights for that) and click the <kbd>teams</kbd> under your event name.
You should see a list of all teams and it's a good idea to have one for all reviewers, e.g. `2023-Reviewers-ALL`. By clicking on the team name you
get to a page that lists the names and corresponding e-mails of team members as well as an option to add new members at the bottom.

You can now start typing in the e-mail addresses from the volunteer sheet to send out invitations to them. After volunteers accept
the invitation they will show up with a user-name and e-mail in the team table. Now, here comes the tricky part that can
cause a lot of confusion. If person A entered in the Google Form the e-mail address `work@mail.com`, and you added this in Pretalx,
it might happen that person A accepts the team invitation with a different Pretalx account that is linked to the e-mail
address `private@mail.com`. In this case, Pretalx will automatically replace `work@mail.com`, which was used for the invitation,
with `private@mail.com` in the Pretalx table of team members.
Unfortunately, Pretalx has no way of automatically tracking this change of mail addresses and this issue, as filed in [#1417], is still unresolved.

To work around this email issue and to be able to later join your volunteer sheet for instance with reviews, it makes sense to introduce
a new column, e.g. "Pretalx mail", where you add the actual Pretalx account e-mail that was used by the invited user.
Additionally, you should have a column for the Pretalx user-name, e.g. "Pretalx user", where you state the user-name
by copying it over from the Pretalx team member table. This user-name column will be useful later to join our volunteer reviewers
with the reviews they did, because the [review-endpoint] of Pretalx only returns the user-name, not the e-mail of a reviewer.
This problem was also discussed in [#1416] and is an intended behaviour.

## 3. Assign Proposals to Reviewers according to their Preferences

[Pretalx] already provides a basic assignment feature so that proposals with the least number of reviews will show up earlier
in the review queue so that they get more reviews. Additionally, Pretalx allows uploading a mapping JSON file so that you can
assign certain proposals to a reviewer matching their preferences with the tracks of the proposals. Also, Pretalx
is working on more elaborate automatic assignment features and some discussion about it can be found in issue [#1331].

[Pytanis] allows you to create JSON mapping files that can be uploaded in [Pretalx] under <kbd>Review</kbd> » <kbd>Assign reviews</kbd>.
Then click <kbd>Actions</kbd> (upper right) » <kbd>Import assignments</kbd> and select the option `Assign proposals to reviewers`,
choose the JSON file and make sure to always set `Replace current assignments` to `Yes`. Overwriting the current assignments
makes sure that the assignment state in Pretalx is always consistent with what you expect. Also, be sure to always back up your assignment files
somewhere in case you need to roll back later on. To make this easy, just name your files `assignments-YYYYMMDD_I.json`,
where `YYYY` is the current year, `MM` the month, `DD` the day in the month and `I` the version increment, e.g. `1` or `2`,
in case you need several assignments throughout the same day.

So how do you create an assignment file using Pytanis? Currently, we have implemented in a notebook an initial simple algorithm
that can be easily run. Fancier algorithms will come in the future and don't hesitate to [contribute].
The main idea of the algorithm is to set a goal of number of reviews for each proposal, e.g. 3 reviews, and a certain buffer, e.g. 1.
This means every proposal is assigned to goal number of reviews + buffer - current review number in case the current review number is not
already equal or greater than the goal number of reviews. Rerunning this assignment frequently helps to avoid overshooting as
the buffer mainly addresses the fact that you will also have inactive reviewers or some that start on the last day before your review
deadline. For each proposal and remaining review, the algorithm assigns the proposals to:

* not a person having already assigned the review for a proposal (no duplicates),
* to a person having a preference for the track with the least amount of current work,
* if no person has a preference for the track of the proposal, assign to someone with not much work.

Be aware that some of your reviewers might have also make proposal submissions. Thus, it might happen by chance that someone gets
assigned his/her own proposal using this approach but luckily Pretalx takes care of that--if the same Pretalx account was used.

This quite simple algorithm can be found in the notebook [10_reviewer-assignment_v1]. It uses Pytanis to pull the submission/proposals
as well as the current reviews from Pretalx and joins them to get an overview of the current state of reviews. Then Pytanis
is used to get the Google sheet of reviewers and their preferences, which is also joined with the data from Pretalx. Then the
aforementioned algorithm is run and the assignment JSON file written.

## 4. Communicate with the Reviewers occasionally for Updates

From time to time, you want to get in contact with your reviewers to remind them of some deadline or just to say
thank you for their work. Pytanis has an easy interface to [HelpDesk] that can be used as an e-mail client. For some
practical examples, just check out the notebook [20_mail_to_reviewers_v1], the [docs about mailing](../usage/mail.md),
as well as the [Pytanis' mail references].

## 5. Track the whole process

During the review process it very important to keep track of review activity to make sure your internal deadlines
for the review process are met. For instance, there might be reviewers that are having difficulties but have not reached out yet.
So finding inactivate reviewers after a certain period of time and sending a nice supportive e-mail helps a lot. Also, some reviewers
might have finished their batch of work early but might be up for more, thus identifying and getting in contact with them,
is always a good idea. Many of those analyses are really individual, and you can check our examples in the notebook [10_reviewer-assignment_v1].


[#1417]: https://github.com/pretalx/pretalx/issues/1417
[#1416]: https://github.com/pretalx/pretalx/issues/1416
[review-endpoint]: https://docs.pretalx.org/api/resources/reviews.html
[#1331]: https://github.com/pretalx/pretalx/issues/1331
[contribute]: ../contributing.md
[10_reviewer-assignment_v1]: https://github.com/FlorianWilhelm/pytanis/blob/main/notebooks/pyconde-pydata-berlin-2023/10_reviewer-assignment_v1.ipynb
[20_mail_to_reviewers_v1]: https://github.com/FlorianWilhelm/pytanis/blob/main/notebooks/pyconde-pydata-berlin-2023/20_mail_to_reviewers_v1.ipynb
[Pytanis' mail references]: ../reference/pytanis/helpdesk/mail.md#pytanis.helpdesk.mail
[Pytanis' google module]: ../reference/pytanis/google.md#pytanis.google
