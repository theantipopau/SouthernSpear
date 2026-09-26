// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveStatusWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/PlayerController.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveHudModel.h"

namespace
{
	// Placeholder palette until the UI style pass; friendly/opposing only, never faction colours.
	FLinearColor ToneColour(ESSObjectiveHudTone Tone)
	{
		switch (Tone)
		{
		case ESSObjectiveHudTone::Friendly:  return FLinearColor(0.25f, 0.6f, 1.f);
		case ESSObjectiveHudTone::Opposing:  return FLinearColor(1.f, 0.3f, 0.25f);
		case ESSObjectiveHudTone::Contested: return FLinearColor(1.f, 0.75f, 0.2f);
		default:                             return FLinearColor(0.85f, 0.85f, 0.85f);
		}
	}

	UTextBlock* MakeText(UWidgetTree* Tree, UVerticalBox* Box, int32 Size)
	{
		UTextBlock* Text = Tree->ConstructWidget<UTextBlock>();
		FSlateFontInfo Font = Text->GetFont();
		Font.Size = Size;
		Text->SetFont(Font);
		Text->SetJustification(ETextJustify::Center);
		Text->SetShadowOffset(FVector2D(1.f, 1.f));
		Text->SetShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.8f));
		Box->AddChildToVerticalBox(Text)->SetHorizontalAlignment(HAlign_Center);
		return Text;
	}
}

bool USSObjectiveStatusWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}

	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>();
	WidgetTree->RootWidget = Root;

	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>();
	UCanvasPanelSlot* BoxSlot = Root->AddChildToCanvas(Box);
	BoxSlot->SetAnchors(FAnchors(0.5f, 0.f));
	BoxSlot->SetAlignment(FVector2D(0.5f, 0.f));
	BoxSlot->SetPosition(FVector2D(0.f, 24.f));
	BoxSlot->SetSize(FVector2D(480.f, 120.f));

	HeaderText = MakeText(WidgetTree, Box, 20);
	ObjectiveText = MakeText(WidgetTree, Box, 16);

	ProgressBar = WidgetTree->ConstructWidget<UProgressBar>();
	UVerticalBoxSlot* BarSlot = Box->AddChildToVerticalBox(ProgressBar);
	BarSlot->SetHorizontalAlignment(HAlign_Fill);
	BarSlot->SetPadding(FMargin(0.f, 4.f));

	ScoreText = MakeText(WidgetTree, Box, 14);
	return true;
}

void USSObjectiveStatusWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	const ASSObjectiveAssaultDirector* Dir = Director.Get();
	if (!Dir || !HeaderText)
	{
		return;
	}

	ESSTeamId ViewerTeam = ESSTeamId::None;
	if (const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(GetOwningPlayer()))
	{
		ViewerTeam = Dir->ToTeamId(Agent->GetGenericTeamId());
	}

	const FSSRoundState& Round = Dir->GetRoundState();
	const ASSObjectiveActor* Active = Dir->GetObjectives().IsValidIndex(Round.ActiveObjectiveIndex)
		? Dir->GetObjectives()[Round.ActiveObjectiveIndex].Get() : nullptr;

	const FSSObjectiveHudModel Model = FSSObjectiveHudModel::Build(
		Round, Active ? &Active->GetObjectiveState() : nullptr,
		Active ? Active->ObjectiveName : FText::GetEmpty(), ViewerTeam);

	HeaderText->SetText(Model.Header);
	ScoreText->SetText(Model.Score);
	const ESlateVisibility ObjectiveVisibility = Model.bShowObjective ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed;
	ObjectiveText->SetVisibility(ObjectiveVisibility);
	ProgressBar->SetVisibility(ObjectiveVisibility);
	ObjectiveText->SetText(Model.Objective);
	ProgressBar->SetPercent(Model.Progress);
	ProgressBar->SetFillColorAndOpacity(ToneColour(Model.ProgressTone));
}
