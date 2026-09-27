// Copyright Southern Spear. All Rights Reserved.

#include "SSRoundBannerWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/PlayerController.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveHudModel.h"
#include "SSUIStyle.h"
#include "Styling/CoreStyle.h"
#include "SSFonts.h"

namespace
{
	constexpr float Hold = 2.6f;

	UTextBlock* BannerText(UWidgetTree* Tree, int32 Size, const FLinearColor& Colour, int32 Spacing)
	{
		UTextBlock* Text = Tree->ConstructWidget<UTextBlock>();
		FSlateFontInfo Font = SSFonts::Display(Size);
		Font.LetterSpacing = Spacing;
		Text->SetFont(Font);
		Text->SetColorAndOpacity(Colour);
		Text->SetJustification(ETextJustify::Center);
		Text->SetShadowOffset(FVector2D(1.f, 2.f));
		Text->SetShadowColorAndOpacity(SSUIStyle::Ink950(0.8f));
		return Text;
	}

	FText Letter(int32 Index) { return FText::FromString(FString::Chr(TEXT('A') + FMath::Clamp(Index, 0, 25))); }
}

void USSRoundBannerWidget::Setup(ASSObjectiveAssaultDirector* InDirector)
{
	Director = InDirector;
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	UVerticalBox* Box = T->ConstructWidget<UVerticalBox>();
	Banner = Box;
	UCanvasPanelSlot* BoxSlot = Root->AddChildToCanvas(Box);
	BoxSlot->SetAnchors(FAnchors(0.5f, 0.32f));
	BoxSlot->SetAlignment(FVector2D(0.5f, 0.5f));
	BoxSlot->SetAutoSize(true);

	UBorder* Plate = T->ConstructWidget<UBorder>();
	Plate->SetBrushColor(SSUIStyle::Ink900(0.72f));
	Plate->SetPadding(FMargin(48.f, 12.f, 48.f, 14.f));
	Box->AddChildToVerticalBox(Plate)->SetHorizontalAlignment(HAlign_Center);
	UVerticalBox* Body = T->ConstructWidget<UVerticalBox>();
	Plate->SetContent(Body);
	TitleText = BannerText(T, 30, SSUIStyle::Sand100(), 220);
	Body->AddChildToVerticalBox(TitleText)->SetHorizontalAlignment(HAlign_Center);
	SubtitleText = BannerText(T, 13, SSUIStyle::Sage200(), 200);
	UVerticalBoxSlot* SubSlot = Body->AddChildToVerticalBox(SubtitleText);
	SubSlot->SetHorizontalAlignment(HAlign_Center);
	SubSlot->SetPadding(FMargin(0.f, 4.f, 0.f, 0.f));

	USizeBox* RuleSize = T->ConstructWidget<USizeBox>();
	RuleSize->SetHeightOverride(3.f);
	ToneRule = T->ConstructWidget<UBorder>();
	ToneRule->SetBrushColor(SSUIStyle::Brass500());
	RuleSize->AddChild(ToneRule);
	UVerticalBoxSlot* RuleSlot = Box->AddChildToVerticalBox(RuleSize);
	RuleSlot->SetHorizontalAlignment(HAlign_Fill);

	Banner->SetVisibility(ESlateVisibility::Collapsed);
}

void USSRoundBannerWidget::Show(const FText& Title, const FText& Subtitle, const FLinearColor& Tone)
{
	TitleText->SetText(Title.ToUpper());
	SubtitleText->SetText(Subtitle.ToUpper());
	ToneRule->SetBrushColor(Tone);
	TitleText->SetColorAndOpacity(Tone == SSUIStyle::Brass500() ? SSUIStyle::Sand100() : Tone);
	ShownFor = 0.f;
	Banner->SetVisibility(ESlateVisibility::HitTestInvisible);
}

void USSRoundBannerWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	const ASSObjectiveAssaultDirector* Dir = Director.Get();
	if (!Dir || !Banner)
	{
		return;
	}

	ESSTeamId ViewerTeam = ESSTeamId::None;
	if (const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(GetOwningPlayer()))
	{
		ViewerTeam = Dir->ToTeamId(Agent->GetGenericTeamId());
	}
	const FSSRoundState& Round = Dir->GetRoundState();
	const TArray<TObjectPtr<ASSObjectiveActor>>& Objectives = Dir->GetObjectives();
	auto NameOf = [&Objectives](int32 Index)
	{
		return Objectives.IsValidIndex(Index) && Objectives[Index] ? Objectives[Index]->ObjectiveName : FText::GetEmpty();
	};

	if (Round.Phase != LastPhase || Round.RoundNumber != LastRound)
	{
		if (Round.Phase == ESSRoundPhase::PreRound)
		{
			Show(FText::Format(NSLOCTEXT("SSBanner", "Round", "Round {0}"), FText::AsNumber(Round.RoundNumber)),
				NSLOCTEXT("SSBanner", "StandBy", "Stand by  ·  deploying"), SSUIStyle::Brass500());
		}
		else if (Round.Phase == ESSRoundPhase::InProgress)
		{
			Show(NSLOCTEXT("SSBanner", "Assault", "Assault"),
				FText::Format(NSLOCTEXT("SSBanner", "Take", "Take objective {0}  ·  {1}"), Letter(Round.ActiveObjectiveIndex), NameOf(Round.ActiveObjectiveIndex)),
				SSUIStyle::Brass500());
		}
		else if (Round.Phase == ESSRoundPhase::PostRound)
		{
			const FSSObjectiveHudModel Model = FSSObjectiveHudModel::Build(Round, nullptr, FText::GetEmpty(), ViewerTeam);
			const FLinearColor Tone = Model.FirstScore > Model.SecondScore ? SSUIStyle::ToneColour(Model.FirstTone)
				: Model.SecondScore > Model.FirstScore ? SSUIStyle::ToneColour(Model.SecondTone) : SSUIStyle::Brass500();
			Show(Model.PhaseLabel, FText::Format(NSLOCTEXT("SSBanner", "Score", "{0} {1}  –  {2} {3}"),
				Model.FirstSide, FText::AsNumber(Model.FirstScore), FText::AsNumber(Model.SecondScore), Model.SecondSide), Tone);
		}
		LastPhase = Round.Phase;
		LastRound = Round.RoundNumber;
		LastActive = Round.ActiveObjectiveIndex;
	}
	else if (Round.Phase == ESSRoundPhase::InProgress && Round.ActiveObjectiveIndex > LastActive && LastActive != INDEX_NONE)
	{
		// The previous objective fell: announce who took it, then the next one.
		const ASSObjectiveActor* Taken = Objectives.IsValidIndex(LastActive) ? Objectives[LastActive].Get() : nullptr;
		const ESSTeamId Owner = Taken ? Taken->GetObjectiveState().OwnerTeam : ESSTeamId::None;
		Show(FText::Format(NSLOCTEXT("SSBanner", "Secured", "Objective {0} secured"), Letter(LastActive)),
			FText::Format(NSLOCTEXT("SSBanner", "By", "{0}  ·  next: {1} {2}"), FSSObjectiveHudModel::TeamWord(Owner, ViewerTeam),
				Letter(Round.ActiveObjectiveIndex), NameOf(Round.ActiveObjectiveIndex)),
			SSUIStyle::ToneColour(FSSObjectiveHudModel::ToneFor(Owner, ViewerTeam)));
		LastActive = Round.ActiveObjectiveIndex;
	}

	// Animate: 0.3 s in (drop and fade), hold, 0.5 s out.
	ShownFor += InDeltaTime;
	if (ShownFor > Hold + 0.5f)
	{
		Banner->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	const float In = FMath::InterpEaseOut(0.f, 1.f, FMath::Clamp(ShownFor / 0.3f, 0.f, 1.f), 3.f);
	const float Out = FMath::Clamp((ShownFor - Hold) / 0.5f, 0.f, 1.f);
	Banner->SetRenderOpacity(In * (1.f - Out));
	Banner->SetRenderTranslation(FVector2D(0.f, (1.f - In) * -18.f));
}
