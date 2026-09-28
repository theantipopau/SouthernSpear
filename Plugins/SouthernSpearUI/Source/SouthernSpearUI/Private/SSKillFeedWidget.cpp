// Copyright Southern Spear. All Rights Reserved.

#include "SSKillFeedWidget.h"

#include "Engine/World.h"
#include "SSKillFeedState.h"
#include "SSLocalHudState.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	FLinearColor NameColour(const USSKillFeedState& State, ESSTeamId Team, bool bLocal)
	{
		if (bLocal)
		{
			return SSPalette::Brass300();
		}
		const bool bFriendly = State.LocalTeam != ESSTeamId::None && Team == State.LocalTeam;
		return bFriendly ? SSPalette::Sage200() : SSPalette::Opfor300();
	}
}

bool USSKillFeedWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Feed: top left (the right edge holds the minimap and objective column; producer: the feed "does push
	// under the mini map"). Below the optional frame-rate counter.
	UVerticalBox* Feed = T->ConstructWidget<UVerticalBox>();
	Pin(Root, Feed, FVector2D(0.f, 0.f), FVector2D(20.f, 34.f));
	for (int32 Index = 0; Index < FSSKillFeedRules::MaxEntries; ++Index)
	{
		FRowWidgets Row;
		Row.Plate = Plate(T, SSPalette::Ink900(0.72f), FMargin(10.f, 4.f));
		UHorizontalBox* Line = T->ConstructWidget<UHorizontalBox>();
		Row.Plate->SetContent(Line);
		Row.Killer = Text(T, 13, true, SSPalette::Sand100(), 40);
		AddH(Line, Row.Killer);
		Row.Weapon = Text(T, 11, true, SSPalette::Sand100(0.85f), 120);
		AddH(Line, Row.Weapon)->SetPadding(FMargin(10.f, 0.f));
		Row.Victim = Text(T, 13, true, SSPalette::Sand100(), 40);
		AddH(Line, Row.Victim);
		AddV(Feed, Row.Plate, Index == 0 ? 0.f : 3.f, HAlign_Left);
		Row.Plate->SetVisibility(ESlateVisibility::Collapsed);
		Keep.Add(Row.Plate);
		Rows.Add(Row);
	}

	// The viewer's own kill: below the crosshair.
	UVerticalBox* Own = T->ConstructWidget<UVerticalBox>();
	Confirm = Own;
	Pin(Root, Own, FVector2D(0.5f, 0.5f), FVector2D(0.f, 96.f));
	UTextBlock* Kicker = Text(T, 12, true, SSPalette::Brass300(), 300);
	Kicker->SetText(NSLOCTEXT("SSKillFeed", "Eliminated", "ELIMINATED"));
	AddV(Own, Kicker, 0.f, HAlign_Center);
	ConfirmName = Text(T, 24, true, SSPalette::Sand100(), 80);
	AddV(Own, ConfirmName, 2.f, HAlign_Center);
	ConfirmWeapon = Text(T, 11, true, SSPalette::Sage400(), 200);
	AddV(Own, ConfirmWeapon, 2.f, HAlign_Center);
	Own->SetVisibility(ESlateVisibility::Collapsed);

	// The viewer's own death: a dark wash and "KILLED IN ACTION", with who and with what, until the
	// class selection opens (FSSKillFeedRules::LocalDeathLifetime; producer request).
	DeathWash = Plate(T, SSPalette::Ink950(0.f), FMargin(0.f));
	Fill(Root, DeathWash);
	DeathWash->SetVisibility(ESlateVisibility::Collapsed);
	UVerticalBox* Kia = T->ConstructWidget<UVerticalBox>();
	Death = Kia;
	Pin(Root, Kia, FVector2D(0.5f, 0.38f), FVector2D(0.f, 0.f));
	AddV(Kia, Rule(T, SSPalette::Opfor500(), 2.f, 360.f), 0.f, HAlign_Center);
	DeathTitle = Text(T, 34, true, SSPalette::Sand100(), 260);
	DeathTitle->SetText(NSLOCTEXT("SSKillFeed", "Kia", "KILLED IN ACTION"));
	AddV(Kia, DeathTitle, 10.f, HAlign_Center);
	DeathBy = Text(T, 14, true, SSPalette::Sage200(), 120);
	AddV(Kia, DeathBy, 6.f, HAlign_Center);
	AddV(Kia, Rule(T, SSPalette::Opfor500(), 2.f, 360.f), 12.f, HAlign_Center);
	Kia->SetVisibility(ESlateVisibility::Collapsed);
	return true;
}

void USSKillFeedWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	const UWorld* World = GetWorld();
	const USSKillFeedState* State = World ? World->GetSubsystem<USSKillFeedState>() : nullptr;
	if (!State)
	{
		return;
	}
	const double Now = World->GetTimeSeconds();
	const TArray<FSSKillFeedEntry> Shown = FSSKillFeedRules::Visible(State->Entries, Now);
	for (int32 Index = 0; Index < Rows.Num(); ++Index)
	{
		FRowWidgets& Row = Rows[Index];
		if (!Shown.IsValidIndex(Index))
		{
			Row.Plate->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}
		const FSSKillFeedEntry& Entry = Shown[Index];
		Row.Plate->SetVisibility(ESlateVisibility::HitTestInvisible);
		// Fade over the last second of the entry's life; the viewer's own lines stay highlighted.
		const float Remaining = static_cast<float>(FSSKillFeedRules::EntryLifetime - (Now - Entry.Time));
		Row.Plate->SetRenderOpacity(FMath::Clamp(Remaining, 0.f, 1.f));
		Row.Plate->SetBrushColor(Entry.bLocalKiller || Entry.bLocalVictim ? SSPalette::Brass500(0.3f) : SSPalette::Ink900(0.72f));
		const bool bSelf = Entry.Killer.IsEmpty() || Entry.Killer == Entry.Victim;
		Row.Killer->SetVisibility(bSelf ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
		Row.Killer->SetText(FText::FromString(Entry.Killer));
		Row.Killer->SetColorAndOpacity(NameColour(*State, Entry.KillerTeam, Entry.bLocalKiller));
		Row.Weapon->SetText(bSelf ? NSLOCTEXT("SSKillFeed", "Self", "DOWN") : FText::FromString(Entry.Weapon.IsEmpty() ? TEXT("—") : Entry.Weapon.ToUpper()));
		Row.Victim->SetText(FText::FromString(Entry.Victim));
		Row.Victim->SetColorAndOpacity(NameColour(*State, Entry.VictimTeam, Entry.bLocalVictim));
	}

	const FSSKillFeedEntry* Mine = FSSKillFeedRules::RecentLocalKill(State->Entries, Now);
	Confirm->SetVisibility(Mine ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (Mine)
	{
		const float Age = static_cast<float>(Now - Mine->Time);
		Confirm->SetRenderOpacity(FMath::Clamp(static_cast<float>(FSSKillFeedRules::LocalKillLifetime) - Age, 0.f, 1.f));
		Confirm->SetRenderScale(FVector2D(1.f + 0.12f * FMath::Clamp(1.f - Age * 5.f, 0.f, 1.f)));
		ConfirmName->SetText(FText::FromString(Mine->Victim.ToUpper()));
		ConfirmWeapon->SetText(FText::FromString(Mine->Weapon.ToUpper()));
	}

	const FSSKillFeedEntry* Died = FSSKillFeedRules::RecentLocalDeath(State->Entries, Now);
	Death->SetVisibility(Died ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	DeathWash->SetVisibility(Died ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (Died)
	{
		const float Age = static_cast<float>(Now - Died->Time);
		const float In = FMath::Clamp(Age / 0.6f, 0.f, 1.f);
		DeathWash->SetBrushColor(SSPalette::Ink950(0.55f * In));
		Death->SetRenderOpacity(In);
		const bool bSelf = Died->Killer.IsEmpty() || Died->Killer == Died->Victim;
		const USSLocalHudState* Hud = World->GetSubsystem<USSLocalHudState>();
		const bool bRedeploy = bSelf && Hud && Hud->LastRedeployTime >= 0.0 && Died->Time - Hud->LastRedeployTime < 3.0;
		DeathTitle->SetText(bRedeploy ? NSLOCTEXT("SSKillFeed", "Redeploying", "RE-DEPLOYING") : NSLOCTEXT("SSKillFeed", "Kia", "KILLED IN ACTION"));
		DeathBy->SetText(bSelf ? FText::GetEmpty()
			: Died->Weapon.IsEmpty() ? FText::Format(NSLOCTEXT("SSKillFeed", "KiaBy", "BY {0}"), FText::FromString(Died->Killer.ToUpper()))
			: FText::Format(NSLOCTEXT("SSKillFeed", "KiaByWith", "BY {0}  ·  {1}"), FText::FromString(Died->Killer.ToUpper()), FText::FromString(Died->Weapon.ToUpper())));
		DeathBy->SetColorAndOpacity(Died->KillerTeam != ESSTeamId::None && Died->KillerTeam == State->LocalTeam ? SSPalette::Sage200() : SSPalette::Opfor300());
	}
}
